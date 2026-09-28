#!/usr/bin/env python3
"""Bancada de tools/collect-clarity-insights — sem rede, sem tocar em data/.

O QUE ESTES TESTES IMPEDEM DE VOLTAR (2026-09-09):

1. O teto proprio de 8 requisicoes por dia. A API da 10 por projeto e por dia e
   nao ha como comprar mais; uma segunda requisicao por execucao dobra o
   consumo, e um laco descuidado (timer + execucao manual + retry) esgotaria a
   cota antes do meio-dia. O teste `test_teto_do_coletor` fica VERMELHO quando o
   guarda e removido — foi provado por mutacao, nao por inspecao.
2. A chamada antiga, byte a byte: a unit de medicao pede `--dimensoes Device` e
   nao pode ser reeditada hoje. A URL, os cabecalhos e o esquema da linha da
   primeira requisicao sao os de antes.
3. A falha da requisicao extra NAO muda o codigo de saida: a unit e `oneshot`
   com dois `ExecStart` sem `-`, e um exit != 0 aqui pularia o coletor do Bing
   e acionaria o alerta do dono por um dado que e opcional.
4. A normalizacao da URL para path e a marcacao `no_acervo`, que e o que faz o
   `top_urls` comparavel com content/pages.json.

A ferramenta e carregada pelo caminho em CLARITY_ALVO quando a variavel existe:
e assim que o mutante (copia sem o teto) e submetido a mesma bancada.
"""
from __future__ import annotations

import datetime as dt
import importlib.machinery
import importlib.util
import io
import json
import os
import pathlib
import re
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stdout

RAIZ = pathlib.Path(__file__).resolve().parent.parent
ALVO = pathlib.Path(os.environ.get("CLARITY_ALVO") or RAIZ / "tools" / "collect-clarity-insights")


def carrega():
    loader = importlib.machinery.SourceFileLoader("collect_clarity_insights", str(ALVO))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


def hoje_utc():
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


HOST = "https://wikijuridica.com.br"


def resposta_device():
    return [
        {"metricName": "Traffic", "information": [
            {"totalSessionCount": 24, "totalBotSessionCount": 4, "distinctUserCount": 24,
             "pagesPerSessionPercentage": 2.07, "Device": "Mobile"},
            {"totalSessionCount": 91, "totalBotSessionCount": 11, "distinctUserCount": 90,
             "pagesPerSessionPercentage": 1.22, "Device": "PC"}]},
        {"metricName": "EngagementTime", "information": [
            {"totalTime": 80, "activeTime": 37, "Device": "Mobile"},
            {"totalTime": 266, "activeTime": 88, "Device": "PC"}]},
    ]


def resposta_url():
    """Forma real da resposta com dimensao URL (ledger de 2026-08-29): a chave
    da linha e `Url`, ha linha com `Url: null`, a URL vem absoluta e pode trazer
    fragmento. A doc oficial mostra numeros como string — uma linha usa isso."""
    a = HOST + "/trabalhista/minimo-proporcional/"
    b = HOST + "/tributario/simples-retencao/#sec-a-sumula-425"
    b2 = HOST + "/tributario/simples-retencao/?utm_source=x"
    c = HOST + "/procedimentos/nit-pis/"
    d = HOST + "/nao-existe/"
    return [
        {"metricName": "Traffic", "information": [
            {"totalSessionCount": 0, "totalBotSessionCount": 0, "distinctUserCount": 1,
             "pagesPerSessionPercentage": 1, "Url": None},
            {"totalSessionCount": 3, "totalBotSessionCount": 0, "distinctUserCount": 1,
             "pagesPerSessionPercentage": 2.6666, "Url": a},
            {"totalSessionCount": "2", "totalBotSessionCount": "1", "distinctUserCount": "2",
             "pagesPerSessionPercentage": "1", "Url": b},
            {"totalSessionCount": 2, "totalBotSessionCount": 0, "distinctUserCount": 2,
             "pagesPerSessionPercentage": 1, "Url": b2},
            {"totalSessionCount": 3, "totalBotSessionCount": 1, "distinctUserCount": 3,
             "pagesPerSessionPercentage": 1, "Url": c},
            {"totalSessionCount": 1, "totalBotSessionCount": 0, "distinctUserCount": 1,
             "pagesPerSessionPercentage": 1, "Url": d}]},
        {"metricName": "EngagementTime", "information": [
            {"totalTime": 1401, "activeTime": 268, "Url": a},
            {"totalTime": 25, "activeTime": 22, "Url": b},
            {"totalTime": 10, "activeTime": 5, "Url": b2},
            {"totalTime": 4, "activeTime": 4, "Url": c}]},
        {"metricName": "ScrollDepth", "information": [
            {"averageScrollDepth": 38, "Url": a},
            {"averageScrollDepth": 60, "Url": b},
            {"averageScrollDepth": 30, "Url": b2},
            {"averageScrollDepth": 19, "Url": c}]},
        {"metricName": "DeadClickCount", "information": [
            {"sessionsCount": 3, "pagesViews": 1, "subTotal": 2, "Url": a},
            {"sessionsCount": 3, "pagesViews": 0, "subTotal": 0, "Url": c}]},
        {"metricName": "RageClickCount", "information": [
            {"sessionsCount": 3, "pagesViews": 0, "subTotal": 1, "Url": b2}]},
    ]


class BuscaFalsa:
    """Substituto de `busca_http`: mesma assinatura, resposta por dimensao,
    falha programavel, e registro de cada chamada para o teste conferir."""

    def __init__(self, respostas=None, falhas=None):
        self.respostas = respostas or {"Device": resposta_device(), "URL": resposta_url()}
        self.falhas = falhas or {}
        self.chamadas = []

    def __call__(self, url, cabecalhos, timeout):
        self.chamadas.append({"url": url, "cabecalhos": cabecalhos, "timeout": timeout})
        dim = dict(p.split("=", 1) for p in url.split("?", 1)[1].split("&"))["dimension1"]
        dim = dim.replace("%2F", "/")
        falha = self.falhas.get(dim)
        if falha is not None:
            raise falha
        return 200, json.loads(json.dumps(self.respostas[dim]))


def http_error(codigo):
    return urllib.error.HTTPError("https://www.clarity.ms/x", codigo, "erro", None, None)


class Bancada(unittest.TestCase):
    def setUp(self):
        self.mod = carrega()
        self._tmp = tempfile.TemporaryDirectory()
        raiz = pathlib.Path(self._tmp.name)
        self.mod.SERIE = raiz / "data" / "ops" / "clarity_insights_daily.jsonl"
        self.mod.CURSOR = raiz / "data" / "ops" / "clarity_insights_state.json"
        self.mod.ENV_LOCAL = raiz / ".env.local"
        self.mod.FONTE_ID = raiz / "webanalytics.go"
        self.mod.FONTE_ID.write_text('package x\n\nconst (\n\tClarityProjectID = "proj-teste"\n)\n',
                                     encoding="utf-8")
        self.mod.ACERVO = raiz / "pages.json"
        self.mod.ACERVO.write_text(json.dumps([
            {"path": "/", "status": "published"},
            {"path": "/trabalhista/minimo-proporcional/", "status": "published"},
            {"path": "/tributario/simples-retencao/", "status": "noindex"},
            {"path": "/procedimentos/nit-pis/", "status": "needs_review"},
        ]), encoding="utf-8")
        self._env_antes = os.environ.get(self.mod.CHAVE)
        os.environ[self.mod.CHAVE] = "token-de-teste"
        self.saida = io.StringIO()

    def tearDown(self):
        if self._env_antes is None:
            os.environ.pop(self.mod.CHAVE, None)
        else:
            os.environ[self.mod.CHAVE] = self._env_antes
        self._tmp.cleanup()

    # -- utilitarios ---------------------------------------------------------

    def roda(self, argv, busca):
        with redirect_stdout(self.saida):
            return self.mod.main(argv, busca=busca)

    def ledger(self):
        if not self.mod.SERIE.exists():
            return []
        return [json.loads(l) for l in self.mod.SERIE.read_text(encoding="utf-8").splitlines() if l.strip()]

    def cursor(self):
        return json.loads(self.mod.CURSOR.read_text(encoding="utf-8"))

    def escreve_cursor(self, requisicoes, dia=None):
        self.mod.CURSOR.parent.mkdir(parents=True, exist_ok=True)
        self.mod.CURSOR.write_text(json.dumps({"dia": dia or hoje_utc(), "requisicoes": requisicoes}),
                                   encoding="utf-8")

    # -- compatibilidade da chamada antiga -------------------------------------

    def test_chamada_antiga_com_sem_url_e_identica_a_de_antes(self):
        busca = BuscaFalsa()
        self.assertEqual(self.roda(["--dias", "3", "--dimensoes", "Device", "--sem-url"], busca), 0)
        self.assertEqual(len(busca.chamadas), 1)
        chamada = busca.chamadas[0]
        self.assertEqual(chamada["url"], self.mod.ENDPOINT + "?numOfDays=3&dimension1=Device")
        # Desde 2026-09-10 o cabecalho leva TAMBEM a identidade de saida: ate
        # entao esta coleta ia como `Python-urllib/3.x` para www.clarity.ms, e o
        # gate `check-identidade-de-saida` nao via porque so avaliava arquivo que
        # DEFINE um User-Agent — ausencia escapava da regua. O resto da chamada
        # (URL, parametros, timeout) continua identico, que e o que este teste
        # de compatibilidade guarda.
        self.assertEqual(chamada["cabecalhos"], {
            "Authorization": "Bearer token-de-teste",
            "Content-Type": "application/json",
            "User-Agent": self.mod.USER_AGENT,
        })
        self.assertEqual(
            self.mod.USER_AGENT,
            "Mozilla/5.0 (compatible; WikijuridicaBot/1.0; "
            "+https://wikijuridica.com.br/bot/; medicao-de-audiencia)")
        self.assertEqual(chamada["timeout"], 60)
        linhas = self.ledger()
        self.assertEqual(len(linhas), 1)
        self.assertEqual(set(linhas[0]), {"schema", "coletado_em", "project_id", "janela_dias",
                                          "dimensoes", "http_status", "fuso", "metricas"})
        self.assertEqual(linhas[0]["dimensoes"], ["Device"])
        self.assertEqual(linhas[0]["project_id"], "proj-teste")
        self.assertEqual(linhas[0]["metricas"], resposta_device())
        cursor = self.cursor()
        self.assertEqual((cursor["dia"], cursor["requisicoes"], cursor["ultimas_dimensoes"]),
                         (hoje_utc(), 1, ["Device"]))

    def test_o_que_a_unit_roda_faz_duas_requisicoes_e_a_primeira_nao_muda(self):
        busca = BuscaFalsa()
        self.assertEqual(self.roda(["--dias", "3", "--dimensoes", "Device"], busca), 0)
        self.assertEqual([c["url"] for c in busca.chamadas],
                         [self.mod.ENDPOINT + "?numOfDays=3&dimension1=Device",
                          self.mod.ENDPOINT + "?numOfDays=3&dimension1=URL"])
        self.assertEqual([c["timeout"] for c in busca.chamadas], [60, 40])
        linhas = self.ledger()
        self.assertEqual([l["dimensoes"] for l in linhas], [["Device"], ["URL"]])
        self.assertNotIn("top_urls", linhas[0])
        self.assertIn("top_urls", linhas[1])
        self.assertIn("derivacao_urls", linhas[1])
        cursor = self.cursor()
        self.assertEqual(cursor["requisicoes"], 2)
        self.assertEqual([r["dimensoes"] for r in cursor["requisicoes_hoje"]], [["Device"], ["URL"]])
        self.assertTrue(all(r["http_status"] == 200 for r in cursor["requisicoes_hoje"]))

    def test_url_ja_pedida_nao_gera_segunda_requisicao(self):
        busca = BuscaFalsa()
        self.assertEqual(self.roda(["--dimensoes", "URL"], busca), 0)
        self.assertEqual(len(busca.chamadas), 1)
        linhas = self.ledger()
        self.assertEqual(len(linhas), 1)
        self.assertEqual(linhas[0]["dimensoes"], ["URL"])
        self.assertIn("top_urls", linhas[0])

    # -- teto diario ------------------------------------------------------------

    def test_teto_do_coletor(self):
        """Com 7 gastas, so a primaria cabe; com 8, nenhuma. Sem o guarda as
        contagens seriam 2 e 2 — e o mutante prova que este teste ve isso."""
        self.escreve_cursor(7)
        busca = BuscaFalsa()
        self.assertEqual(self.roda(["--dimensoes", "Device"], busca), 0)
        self.assertEqual(len(busca.chamadas), 1, "com 7 gastas so a primaria pode sair")
        self.assertEqual(busca.chamadas[0]["url"], self.mod.ENDPOINT + "?numOfDays=3&dimension1=Device")
        self.assertEqual(self.cursor()["requisicoes"], 8)
        self.assertEqual([l["dimensoes"] for l in self.ledger()], [["Device"]])
        self.assertIn("teto do coletor atingido", self.saida.getvalue())

        self.escreve_cursor(8)
        busca = BuscaFalsa()
        self.assertEqual(self.roda(["--dimensoes", "Device"], busca), 0)
        self.assertEqual(len(busca.chamadas), 0, "com 8 gastas nada sai")
        self.assertEqual(self.cursor()["requisicoes"], 8)
        self.assertEqual(len(self.ledger()), 1, "nada novo no ledger")

    def test_teto_e_por_dia_utc(self):
        self.escreve_cursor(8, dia="2000-01-01")
        busca = BuscaFalsa()
        self.assertEqual(self.roda(["--dimensoes", "Device"], busca), 0)
        self.assertEqual(len(busca.chamadas), 2)
        cursor = self.cursor()
        self.assertEqual((cursor["dia"], cursor["requisicoes"]), (hoje_utc(), 2))
        self.assertEqual(len(cursor["requisicoes_hoje"]), 2, "a lista do dia anterior nao vaza")

    def test_recusa_da_api_conta_como_requisicao(self):
        busca = BuscaFalsa(falhas={"URL": http_error(400)})
        self.assertEqual(self.roda(["--dimensoes", "Device"], busca), 0,
                         "a extra falhou; o exit e o da primaria, que passou")
        self.assertEqual(len(busca.chamadas), 2)
        cursor = self.cursor()
        self.assertEqual(cursor["requisicoes"], 2, "400 tambem consome cota")
        self.assertEqual(cursor["ultimo_erro"]["codigo"], 400)
        self.assertEqual(cursor["ultimo_erro"]["dimensoes"], ["URL"])
        self.assertEqual([l["dimensoes"] for l in self.ledger()], [["Device"]])
        self.assertIn("REPROVADO", self.saida.getvalue())

    def test_falha_da_primaria_devolve_1_e_nao_tenta_a_extra(self):
        busca = BuscaFalsa(falhas={"Device": http_error(401)})
        self.assertEqual(self.roda(["--dimensoes", "Device"], busca), 1)
        self.assertEqual(len(busca.chamadas), 1)
        self.assertEqual(self.cursor()["requisicoes"], 1)
        self.assertEqual(self.ledger(), [])

    def test_falha_de_rede_nao_conta_e_reprova(self):
        busca = BuscaFalsa(falhas={"Device": urllib.error.URLError("sem rota")})
        self.assertEqual(self.roda(["--dimensoes", "Device"], busca), 1)
        self.assertFalse(self.mod.CURSOR.exists(), "nao chegou na API: nada a contar")

    def test_linha_identica_no_mesmo_dia_nao_se_regrava_mas_conta(self):
        busca = BuscaFalsa()
        self.assertEqual(self.roda(["--dimensoes", "Device"], busca), 0)
        self.assertEqual(self.roda(["--dimensoes", "Device"], busca), 0)
        self.assertEqual(len(busca.chamadas), 4)
        self.assertEqual([l["dimensoes"] for l in self.ledger()], [["Device"], ["URL"]])
        self.assertEqual(self.cursor()["requisicoes"], 4)
        self.assertIn("nao regravada", self.saida.getvalue())

    def test_linha_identica_de_ontem_nao_suprime_a_de_hoje(self):
        """Prova a fronteira do dia — e e sobre ela que a leitura do ledger para
        de fazer parse do historico inteiro."""
        ontem = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1)).isoformat()
        self.mod.SERIE.parent.mkdir(parents=True, exist_ok=True)
        self.mod.SERIE.write_text(json.dumps({
            "schema": "clarity_insights_v1", "coletado_em": ontem, "project_id": "proj-teste",
            "janela_dias": 3, "dimensoes": ["Device"], "http_status": 200, "fuso": "UTC",
            "metricas": resposta_device()}) + "\n", encoding="utf-8")
        self.assertEqual(self.roda(["--dimensoes", "Device", "--sem-url"], BuscaFalsa()), 0)
        linhas = self.ledger()
        self.assertEqual(len(linhas), 2, "a de ontem nao vale como a de hoje")
        self.assertEqual(linhas[1]["coletado_em"][:10], hoje_utc())
        self.assertNotIn("nao regravada", self.saida.getvalue())
        self.assertIsNone(self.mod.ultima_linha_equivalente(hoje_utc(), ["URL"]))
        self.assertEqual(self.mod.ultima_linha_equivalente(hoje_utc(), ["Device"])["coletado_em"],
                         linhas[1]["coletado_em"])

    def test_acervo_ilegivel_nao_muda_exit_nem_perde_a_contagem(self):
        """pages.json e reescrito pela publicacao; se estiver quebrado na hora da
        coleta, a linha de URL entra crua com o erro nomeado, a requisicao fica
        contada e o exit continua o da primaria — a unit encadeia o Bing."""
        self.mod.ACERVO.write_text("{ isto nao e json", encoding="utf-8")
        busca = BuscaFalsa()
        self.assertEqual(self.roda(["--dimensoes", "Device"], busca), 0)
        self.assertEqual(len(busca.chamadas), 2)
        self.assertEqual(self.cursor()["requisicoes"], 2, "contada antes da derivacao")
        linhas = self.ledger()
        self.assertEqual([l["dimensoes"] for l in linhas], [["Device"], ["URL"]])
        self.assertNotIn("top_urls", linhas[1])
        self.assertIn("JSONDecodeError", linhas[1]["derivacao_urls"]["erro"])
        self.assertEqual(linhas[1]["metricas"], resposta_url())
        self.assertIn("REPROVADO: derivacao de top_urls falhou", self.saida.getvalue())

        # Falha de novo com as mesmas metricas: linha crua identica, nao regrava.
        self.mod.ACERVO.unlink()
        self.assertEqual(self.roda(["--dimensoes", "URL"], BuscaFalsa()), 0)
        self.assertEqual(len(self.ledger()), 2, "crua identica a crua: nao regrava")
        self.assertEqual(self.cursor()["requisicoes"], 3, "mas a requisicao conta")
        self.assertIn("FileNotFoundError", self.saida.getvalue())

        # Acervo de volta: a linha derivada NAO e identica a crua e entra —
        # senao a primeira falha do dia deixaria o dia sem top_urls.
        self.mod.ACERVO.write_text(json.dumps([{"path": "/procedimentos/nit-pis/"}]), encoding="utf-8")
        self.assertEqual(self.roda(["--dimensoes", "URL"], BuscaFalsa()), 0)
        linhas = self.ledger()
        self.assertEqual(len(linhas), 3)
        self.assertIn("top_urls", linhas[2])
        self.assertEqual(linhas[2]["derivacao_urls"]["acervo_paths"], 1)
        self.assertEqual(self.cursor()["requisicoes"], 4)
        # E a derivada repetida volta a ser identica.
        self.assertEqual(self.roda(["--dimensoes", "URL"], BuscaFalsa()), 0)
        self.assertEqual(len(self.ledger()), 3)

    # -- normalizacao ----------------------------------------------------------

    def test_normaliza_path(self):
        n = self.mod.normaliza_path
        self.assertEqual(n(HOST + "/a/b/"), "/a/b/")
        self.assertEqual(n(HOST + "/a/b/?utm_source=x&q=1"), "/a/b/")
        self.assertEqual(n(HOST + "/a/b/#sec-1"), "/a/b/")
        self.assertEqual(n(HOST + "/a/b/?x=1#frag"), "/a/b/")
        self.assertEqual(n("http://wikijuridica.com.br/a/b"), "/a/b", "barra final nao se inventa")
        self.assertEqual(n(HOST), "/")
        self.assertEqual(n(HOST + "/"), "/")
        self.assertEqual(n(HOST + "/tribut%C3%A1rio/"), "/tributário/")
        self.assertEqual(n("wikijuridica.com.br/x/?a=1"), "/x/", "sem esquema: host cai, query nao vaza")
        self.assertEqual(n("/ja/path/?a=1"), "/ja/path/")
        self.assertIsNone(n(None))
        self.assertIsNone(n(""))
        self.assertIsNone(n("   "))

    def test_no_acervo(self):
        acervo = {"/a/", "/b/c/"}
        self.assertTrue(self.mod.no_acervo("/a/", acervo))
        self.assertTrue(self.mod.no_acervo("/a", acervo), "/a e /a/ sao a mesma pagina na borda")
        self.assertTrue(self.mod.no_acervo("/b/c/", acervo))
        self.assertFalse(self.mod.no_acervo("/b/", acervo))
        self.assertFalse(self.mod.no_acervo("/a/index.md", acervo))
        self.assertFalse(self.mod.no_acervo("/", acervo))

    def test_carrega_acervo_le_a_lista_de_paginas(self):
        acervo = self.mod.carrega_acervo()
        self.assertEqual(acervo, {"/", "/trabalhista/minimo-proporcional/",
                                  "/tributario/simples-retencao/", "/procedimentos/nit-pis/"})
        self.mod.ACERVO.write_text('{"nao": "lista"}', encoding="utf-8")
        with self.assertRaises(ValueError):
            self.mod.carrega_acervo()

    # -- top_urls ----------------------------------------------------------------

    def test_deriva_top_urls_agrega_ordena_e_marca_acervo(self):
        acervo = self.mod.carrega_acervo()
        top, resumo = self.mod.deriva_top_urls(resposta_url(), acervo)
        self.assertEqual([t["url"] for t in top],
                         ["/tributario/simples-retencao/",      # 2+2 sessoes (fragmento + query)
                          "/procedimentos/nit-pis/",            # 3 sessoes, 3 usuarios
                          "/trabalhista/minimo-proporcional/",  # 3 sessoes, 1 usuario
                          "/nao-existe/"])                       # 1 sessao
        simples = top[0]
        self.assertEqual((simples["sessoes"], simples["sessoes_bot"], simples["usuarios"], simples["variantes"]),
                         (4, 1, 4, 2))
        self.assertEqual((simples["tempo_total_s"], simples["tempo_ativo_s"]), (35, 27))
        self.assertEqual(simples["scroll_medio"], 45.0, "60 e 30 ponderados por 2 e 2 sessoes")
        self.assertEqual(simples["rage_clicks"], 1)
        self.assertEqual(simples["paginas_por_sessao"], 1.0)
        self.assertTrue(simples["no_acervo"], "noindex ainda e acervo")
        self.assertEqual(top[2]["dead_clicks"], 2)
        self.assertEqual(top[2]["paginas_por_sessao"], 2.6666)
        self.assertFalse(top[3]["no_acervo"])
        self.assertNotIn("pageviews", simples, "a API nao da pageviews por URL; nao se inventa")
        self.assertEqual(resumo, {"paths_distintos": 4, "linhas_sem_url": 1, "sessoes_sem_url": 0,
                                  "linhas_max_por_metrica": 6, "truncado_1000": False,
                                  "acervo_paths": 4, "fora_do_acervo": 1})

    def test_deriva_top_urls_ordem_deterministica_e_teto_de_100(self):
        linhas = []
        for i in range(150):
            # sessoes crescem com i, entao a ordem esperada e decrescente em i;
            # dois paths empatam em sessoes e usuarios para provar o desempate
            # por path.
            linhas.append({"totalSessionCount": i // 2, "totalBotSessionCount": 0,
                           "distinctUserCount": 1, "pagesPerSessionPercentage": 1,
                           "Url": HOST + f"/p/{i:03d}/"})
        bruto = [{"metricName": "Traffic", "information": linhas}]
        top, resumo = self.mod.deriva_top_urls(bruto, set())
        self.assertEqual(len(top), 100)
        self.assertEqual(resumo["paths_distintos"], 150)
        sessoes = [t["sessoes"] for t in top]
        self.assertEqual(sessoes, sorted(sessoes, reverse=True))
        self.assertEqual(top[0]["url"], "/p/148/", "empate 148/149 em sessoes e usuarios: path menor primeiro")
        self.assertEqual(top[1]["url"], "/p/149/")
        self.assertTrue(all(not t["no_acervo"] for t in top))
        # A mesma entrada em ordem embaralhada produz a mesma saida.
        bruto2 = [{"metricName": "Traffic", "information": list(reversed(linhas))}]
        top2, _ = self.mod.deriva_top_urls(bruto2, set())
        self.assertEqual(top, top2)

    def test_deriva_top_urls_sinaliza_resposta_truncada(self):
        linhas = [{"totalSessionCount": 1, "totalBotSessionCount": 0, "distinctUserCount": 1,
                   "pagesPerSessionPercentage": 1, "Url": HOST + f"/t/{i}/"} for i in range(1000)]
        _, resumo = self.mod.deriva_top_urls([{"metricName": "Traffic", "information": linhas}], set())
        self.assertTrue(resumo["truncado_1000"])
        self.assertEqual(resumo["linhas_max_por_metrica"], 1000)

    def test_deriva_top_urls_tolera_resposta_fora_da_forma(self):
        self.assertEqual(self.mod.deriva_top_urls({"erro": "x"}, set()),
                         ([], {"paths_distintos": 0, "linhas_sem_url": 0, "sessoes_sem_url": 0,
                               "linhas_max_por_metrica": 0, "truncado_1000": False,
                               "acervo_paths": 0, "fora_do_acervo": 0}))

    def test_linha_de_url_no_ledger_traz_top_urls_ordenado(self):
        self.roda(["--dimensoes", "Device"], BuscaFalsa())
        linha = self.ledger()[1]
        self.assertEqual(linha["dimensoes"], ["URL"])
        self.assertEqual([t["url"] for t in linha["top_urls"]][:2],
                         ["/tributario/simples-retencao/", "/procedimentos/nit-pis/"])
        self.assertEqual(linha["derivacao_urls"]["acervo_fonte"], str(self.mod.ACERVO),
                         "fora da raiz do repo o caminho sai absoluto; dentro dela, relativo")
        self.assertEqual(self.mod._rel(self.mod.RAIZ / "content" / "pages.json"), "content/pages.json")
        self.assertEqual(linha["derivacao_urls"]["fora_do_acervo"], 1)
        self.assertIn("/nao-existe/", self.saida.getvalue())
        self.assertIn("(fora do acervo)", self.saida.getvalue())


class IdentidadeDeSaida(unittest.TestCase):
    """O UNICO teste que exercita `busca_http`, o caminho real de rede.

    Os demais injetam `busca` e por isso nunca veem um cabecalho: foi por esse
    buraco que a ferramenta saiu como `Python-urllib/3.x` para www.clarity.ms
    ate 2026-09-10, sem nenhum gate acusar — `check-identidade-de-saida` so
    avaliava arquivo que DEFINE um User-Agent, e ausencia escapava da regua.

    A rede e dublada UM NIVEL ABAIXO, em `urllib.request.urlopen`, para que o
    `Request` montado pela ferramenta possa ser lido. Nada sai da maquina.

    PROVA POR MUTACAO: apagar `"User-Agent": USER_AGENT` de `requisita` deixa
    este teste vermelho. Para ver sem tocar na ferramenta:

      cp tools/collect-clarity-insights /tmp/x
      sed -i 's/,\n *"User-Agent": USER_AGENT//' /tmp/x   # ou remova a linha
      CLARITY_ALVO=/tmp/x python3 tools/test_collect_clarity_insights.py
    """

    CANONICO = re.compile(
        r"^Mozilla/5\.0 \(compatible; WikijuridicaBot/\d+\.\d+; "
        r"\+https://wikijuridica\.com\.br/bot/; [a-z0-9][a-z0-9 .,:/-]*\)$")

    def setUp(self):
        self.mod = carrega()

    def test_requisicao_real_sai_como_wikijuridicabot(self):
        capturadas = []

        class RespostaFalsa(io.BytesIO):
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *_):
                self.close()
                return False

        def falso_urlopen(requisicao, timeout=None):
            capturadas.append(requisicao)
            return RespostaFalsa(b'{"ok": true}')

        original = self.mod.urllib.request.urlopen
        self.mod.urllib.request.urlopen = falso_urlopen
        try:
            self.mod.requisita("token-de-teste", 3, ["Device"], 10, self.mod.busca_http)
        finally:
            self.mod.urllib.request.urlopen = original

        self.assertEqual(len(capturadas), 1)
        # urllib normaliza o nome do cabecalho para "User-agent".
        enviado = capturadas[0].get_header("User-agent")
        self.assertIsNotNone(
            enviado, "a requisicao saiu sem User-Agent: o urllib mandaria Python-urllib")
        self.assertNotIn("Python-urllib", enviado)
        self.assertRegex(enviado, self.CANONICO)

    def test_proposito_declara_medicao_de_audiencia(self):
        """O proposito nao e decorativo: ele diz ao operador do outro lado o que
        a saida faz. Esta LE a metrica do nosso proprio projeto no Clarity — nao
        e coleta de fonte oficial nem submissao de URL."""
        self.assertTrue(self.mod.USER_AGENT.endswith("; medicao-de-audiencia)"),
                        self.mod.USER_AGENT)

    def test_nao_se_apresenta_como_navegador_nem_como_bot_de_terceiro(self):
        ua = self.mod.USER_AGENT
        for proibido in ("Chrome/", "Safari/", "Firefox/", "Edg/",
                         "Googlebot", "GPTBot", "ClaudeBot", "bingbot"):
            self.assertNotIn(proibido, ua)


if __name__ == "__main__":
    unittest.main()
