#!/usr/bin/env python3
"""Prova, SEM nenhuma requisicao de rede, os blocos por URL de
`collect-bing-webmaster` (2026-09-09): parsing das datas do WCF, stride
deterministico da janela diaria de GetUrlInfo, retomada do cursor no mesmo dia,
topo por impressoes e o teto de requisicoes por execucao.

A rede e substituida por uma funcao `busca` injetada em `main(...)`; o ledger,
o cursor, o manifesto e o site.json apontam para um diretorio temporario por
teste. Cada teste carrega uma copia fresca do modulo para que um monkeypatch
nao vaze entre eles.

Cada teste abaixo falha contra o coletor anterior a 2026-09-09, que so tinha os
cinco blocos de site — e falha tambem contra mutacoes especificas:
  - `test_teto_corta_e_o_cursor_retoma_no_mesmo_dia` fica vermelho se
    `Orcamento.gasta` deixar de contar ou se `seleciona_urlinfo` ignorar `feitas`.
  - `test_janela_e_a_mesma_no_mesmo_dia_e_anda_no_dia_seguinte` fica vermelho se
    o inicio da janela sair de `random`, do relogio ou do cursor.
  - `test_min_value_vira_none` fica vermelho se `normaliza` voltar a devolver
    `0001-01-01` — o que faria o submit tratar "nunca" como "ha 2.025 anos".
  - `test_ritmo_segura_10_por_janela_de_62_s` fica vermelho se `Ritmo.antes`
    deixar de esperar — e a 11a chamada em 60 s e o que a API recusa com
    ThrottleHost (medido em 2026-09-09).
  - `test_throttle_host_recua_a_janela_e_repete_o_item` fica vermelho se o 400
    de ThrottleHost voltar a contar como falha comum.
  - `test_tempo_maximo_corta_e_o_cursor_retoma` fica vermelho se o teto de
    tempo sumir — e e ele que mantem o run padrao abaixo do `timeout 120` da
    unit de medicao externa.
  - `test_cada_bloco_descarrega_no_ledger_antes_do_seguinte` fica vermelho se a
    gravacao voltar para o fim de `main`: um SIGTERM no minuto 30 do run
    noturno perderia tudo que a API ja tinha devolvido.

O relogio e injetado: cada chamada a API "leva" 1 s e cada espera avanca o
relogio pelo que foi pedido, entao 200 URLs custam ~20 min de tempo simulado
e zero de tempo real.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import importlib.util
import io
import json
import os
import pathlib
import tempfile
import re
import unittest
import urllib.error
import urllib.parse
from importlib.machinery import SourceFileLoader

RAIZ = pathlib.Path(__file__).resolve().parent.parent
_ALVO = os.environ.get("WIKI_BING_COLETOR_ALVO") or str(RAIZ / "tools" / "collect-bing-webmaster")
BASE = "https://exemplo.test"
DIA = dt.datetime(2026, 9, 9, 3, 10, tzinfo=dt.timezone.utc)


def _carrega_modulo_fresco():
    loader = SourceFileLoader("collect_bing_webmaster_test_subject", _ALVO)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


def _wcf(data: dt.date) -> str:
    epoch = int(dt.datetime(data.year, data.month, data.day, tzinfo=dt.timezone.utc).timestamp())
    return f"/Date({epoch * 1000})/"


class ApiFalsa:
    """Responde como o Bing responde (formato medido em 2026-09-09) e conta
    cada chamada por endpoint. `derruba_em` faz a n-esima chamada de um
    endpoint devolver HTTP 500, para exercitar o laco de falhas."""

    LATENCIA_S = 1.0

    def __init__(self, paginas_rastreadas=(), derruba=None, estrangula_em=()):
        self.chamadas = []
        self.rastreadas = set(paginas_rastreadas)
        self.derruba = derruba or {}
        # Numeros de chamada (1-based, todas contadas) que devolvem ThrottleHost.
        self.estrangula_em = set(estrangula_em)
        self.agora = 1000.0
        self.esperas = []

    def relogio(self):
        return self.agora

    def espera(self, segundos):
        self.esperas.append(round(segundos, 3))
        self.agora += segundos

    def __call__(self, url):
        partes = urllib.parse.urlsplit(url)
        endpoint = partes.path.rsplit("/", 1)[-1]
        parametros = dict(urllib.parse.parse_qsl(partes.query))
        self.chamadas.append((endpoint, parametros))
        self.agora += self.LATENCIA_S
        if len(self.chamadas) in self.estrangula_em:
            raise urllib.error.HTTPError(url, 400, "Bad Request", {},
                                         io.BytesIO(b'{"ErrorCode":5,"Message":"ERROR!!! ThrottleHost"}'))
        vez = sum(1 for e, _ in self.chamadas if e == endpoint)
        if self.derruba.get(endpoint) == vez:
            raise urllib.error.HTTPError(url, 500, "falha simulada", {}, io.BytesIO(b""))
        if endpoint == "GetUrlInfo":
            alvo = parametros["url"]
            rastreada = alvo in self.rastreadas
            return {"d": {"__type": "UrlInfo:#Microsoft.Bing.Webmaster.Api",
                          "AnchorCount": 3 if rastreada else 0,
                          "DiscoveryDate": _wcf(dt.date(2026, 8, 20)) if rastreada else "/Date(-62135596800000)/",
                          "DocumentSize": 23888 if rastreada else 0,
                          "HttpStatus": 0, "IsPage": True,
                          "LastCrawledDate": _wcf(dt.date(2026, 9, 1)) if rastreada else "/Date(-62135596800000)/",
                          "TotalChildUrlCount": 0, "Url": alvo}}
        if endpoint == "GetQueryStats":
            return {"d": [
                {"__type": "QueryStats:#Microsoft.Bing.Webmaster.Api", "Query": "pensao alimenticia",
                 "Impressions": 5, "Clicks": 1, "Date": _wcf(dt.date(2026, 9, 4)),
                 "AvgImpressionPosition": 3, "AvgClickPosition": 2},
                {"__type": "QueryStats:#Microsoft.Bing.Webmaster.Api", "Query": "pensao alimenticia",
                 "Impressions": 4, "Clicks": 0, "Date": _wcf(dt.date(2026, 8, 28)),
                 "AvgImpressionPosition": 4, "AvgClickPosition": -1},
                {"__type": "QueryStats:#Microsoft.Bing.Webmaster.Api", "Query": "wiki juridica",
                 "Impressions": 6, "Clicks": 0, "Date": _wcf(dt.date(2026, 9, 4)),
                 "AvgImpressionPosition": 1, "AvgClickPosition": -1},
                {"__type": "QueryStats:#Microsoft.Bing.Webmaster.Api", "Query": "aviso previo",
                 "Impressions": 1, "Clicks": 0, "Date": _wcf(dt.date(2026, 9, 4)),
                 "AvgImpressionPosition": 9, "AvgClickPosition": -1},
            ]}
        if endpoint == "GetPageStats":
            return {"d": [
                {"__type": "QueryStats:#Microsoft.Bing.Webmaster.Api", "Query": f"{BASE}/familia/pensao/",
                 "Impressions": 7, "Clicks": 1, "Date": _wcf(dt.date(2026, 9, 4)),
                 "AvgImpressionPosition": 3, "AvgClickPosition": 2},
                {"__type": "QueryStats:#Microsoft.Bing.Webmaster.Api", "Query": f"{BASE}/",
                 "Impressions": 2, "Clicks": 0, "Date": _wcf(dt.date(2026, 9, 4)),
                 "AvgImpressionPosition": 1, "AvgClickPosition": -1},
            ]}
        if endpoint == "GetQueryPageStats":
            return {"d": [{"__type": "QueryStats:#Microsoft.Bing.Webmaster.Api",
                           "Query": f"{BASE}/familia/pensao/", "Impressions": 2, "Clicks": 0,
                           "Date": _wcf(dt.date(2026, 9, 4)), "AvgImpressionPosition": 3,
                           "AvgClickPosition": -1}]}
        if endpoint == "GetPageQueryStats":
            return {"d": [{"__type": "QueryStats:#Microsoft.Bing.Webmaster.Api",
                           "Query": "pensao alimenticia", "Impressions": 2, "Clicks": 0,
                           "Date": _wcf(dt.date(2026, 9, 4)), "AvgImpressionPosition": 3,
                           "AvgClickPosition": -1}]}
        if endpoint in ("GetRankAndTrafficStats", "GetCrawlStats"):
            return {"d": [{"__type": "x", "Date": _wcf(dt.date(2026, 9, 8)), "Clicks": 1, "Impressions": 9}]}
        if endpoint == "GetCrawlIssues":
            return {"d": []}
        raise AssertionError(f"endpoint inesperado no teste: {endpoint}")


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        raiz = pathlib.Path(self.tmp.name)
        self.modulo = _carrega_modulo_fresco()
        self.modulo.SITE = raiz / "site.json"
        self.modulo.SERIE = raiz / "bing_webmaster_daily.jsonl"
        self.modulo.CURSOR = raiz / "bing_webmaster_state.json"
        self.modulo.MANIFESTO = raiz / "published_manifest.jsonl"
        self.modulo.ENV_LOCAL = raiz / ".env.local"
        self.modulo.SITE.write_text(json.dumps({"base_url": BASE}), encoding="utf-8")
        self.paths = [f"/area{i % 7}/pagina-{i:03d}/" for i in range(500)]
        with open(self.modulo.MANIFESTO, "w", encoding="utf-8") as h:
            for i, path in enumerate(self.paths):
                h.write(json.dumps({"unique_intent_id": f"int-{i}", "path": path,
                                    "canonical_url": BASE + path, "page_status": "published",
                                    "approved_at": "2026-08-06"}) + "\n")
            # Linha duplicada por unique_intent_id: o manifesto real e 1:1, mas o
            # coletor desduplica por construcao.
            h.write(json.dumps({"unique_intent_id": "int-0", "path": self.paths[0],
                                "canonical_url": BASE + self.paths[0], "page_status": "published"}) + "\n")
        os.environ[self.modulo.CHAVE] = "chave-de-teste"

    def tearDown(self):
        os.environ.pop(self.modulo.CHAVE, None)
        self.tmp.cleanup()

    def roda(self, argv, api, agora=DIA, tempo_maximo=None):
        """`tempo_maximo` None = folga (1e6 s) para o teste medir outra coisa;
        o padrao real da ferramenta (100 s) so entra quando o teste o pede."""
        if tempo_maximo is None:
            argv = list(argv) + ["--tempo-maximo", "1000000"]
        elif tempo_maximo != "padrao":
            argv = list(argv) + ["--tempo-maximo", str(tempo_maximo)]
        saida = io.StringIO()
        relogio = getattr(api, "relogio", None)
        espera = getattr(api, "espera", None)
        with contextlib.redirect_stdout(saida):
            if relogio is None:
                codigo = self.modulo.main(argv, busca=api, agora=agora,
                                          relogio=lambda: 0.0, espera=lambda s: None)
            else:
                codigo = self.modulo.main(argv, busca=api, agora=agora, relogio=relogio, espera=espera)
        return codigo, saida.getvalue()

    def linhas(self, tipo=None):
        if not self.modulo.SERIE.exists():
            return []
        registros = [json.loads(l) for l in self.modulo.SERIE.read_text(encoding="utf-8").splitlines() if l.strip()]
        return [r for r in registros if tipo is None or r["tipo"] == tipo]

    def estado(self):
        return json.loads(self.modulo.CURSOR.read_text(encoding="utf-8"))


class TestDatas(Base):
    def test_parse_de_data_wcf_fica_em_utc_e_ignora_o_fuso_do_painel(self):
        n = self.modulo.normaliza
        self.assertEqual(n("/Date(1788650167000)/"), "2026-09-05")
        # O sufixo -0700 e so o fuso em que o painel exibe; nao move o dia.
        self.assertEqual(n("/Date(1786345200000-0700)/"), n("/Date(1786345200000)/"))
        self.assertEqual(n("/Date(1786345200000+0530)/"), n("/Date(1786345200000)/"))
        self.assertEqual(n(23888), 23888)
        self.assertEqual(n("wiki juridica"), "wiki juridica")
        self.assertIs(n(True), True)

    def test_min_value_vira_none(self):
        # Medido em 2026-09-09: GetUrlInfo de URL nunca visitada devolve
        # DateTime.MinValue em LastCrawledDate e DiscoveryDate.
        self.assertIsNone(self.modulo.normaliza("/Date(-62135596800000)/"))
        self.assertIsNone(self.modulo.normaliza("/Date(-62135596800000-0700)/"))
        # Epoch negativo comum (antes de 1970) continua sendo data.
        self.assertEqual(self.modulo.normaliza("/Date(-86400000)/"), "1969-12-31")


class TestStride(Base):
    def test_janela_e_a_mesma_no_mesmo_dia_e_anda_no_dia_seguinte(self):
        m = self.modulo
        paginas = m.carrega_manifesto()
        self.assertEqual(len(paginas), 500, "desduplica por unique_intent_id")
        hashes = [__import__("hashlib").sha256(p.encode()).hexdigest() for p, _ in paginas]
        self.assertEqual(hashes, sorted(hashes), "ordem por sha256(path)")

        hoje = dt.date(2026, 9, 9)
        i1, f1, p1 = m.seleciona_urlinfo(paginas, hoje, None)
        i2, f2, p2 = m.seleciona_urlinfo(paginas, hoje, {})
        self.assertEqual((i1, f1, p1), (i2, f2, p2), "mesmo dia, mesma janela, sem estado")
        self.assertEqual(len(p1), 200)
        self.assertEqual(i1, (hoje.toordinal() * 200) % 500)

        i3, _, p3 = m.seleciona_urlinfo(paginas, hoje + dt.timedelta(days=1), None)
        self.assertEqual(i3, (i1 + 200) % 500, "o dia seguinte comeca onde o de hoje acabou")
        self.assertFalse(set(p1) & set(p3), "janelas de dias seguidos nao se sobrepoem")

        # Em 3 dias (600 > 500) a janela da a volta e cobre o acervo inteiro.
        cobertas = set()
        for d in range(3):
            _, _, p = m.seleciona_urlinfo(paginas, hoje + dt.timedelta(days=d), None)
            cobertas |= set(p)
        self.assertEqual(len(cobertas), 500)

    def test_acervo_menor_que_a_janela_vira_a_janela_inteira(self):
        m = self.modulo
        paginas = m.carrega_manifesto()[:30]
        _, _, pendentes = m.seleciona_urlinfo(paginas, dt.date(2026, 9, 9), None)
        self.assertEqual(sorted(pendentes), sorted(paginas))


class TestTopo(Base):
    def test_topo_soma_impressoes_por_chave_e_desempata_pela_chave(self):
        api = ApiFalsa()
        registros = api(f"{BASE}/x/GetQueryStats?a=b")["d"]
        topo = self.modulo.topo_por_impressoes(registros)
        # pensao alimenticia soma 9 nas duas semanas e passa "wiki juridica" (6).
        self.assertEqual(topo, ["pensao alimenticia", "wiki juridica", "aviso previo"])
        self.assertEqual(self.modulo.topo_por_impressoes(registros, topo=1), ["pensao alimenticia"])
        empate = [{"Query": "b", "Impressions": 1}, {"Query": "a", "Impressions": 1}]
        self.assertEqual(self.modulo.topo_por_impressoes(empate), ["a", "b"])


class TestRitmo(Base):
    def test_ritmo_segura_10_por_janela_de_62_s(self):
        api = ApiFalsa()
        codigo, _ = self.roda(["--so", "urlinfo", "--max-requisicoes", "25"], api)
        self.assertEqual(codigo, 0)
        self.assertEqual(len(api.chamadas), 25)
        # 10 chamadas a 1 s cada ocupam 10 s; a 11a espera os 52 s que faltam
        # para a 1a sair da janela de 62 s; idem a 21a.
        self.assertEqual(len(api.esperas), 2)
        self.assertEqual(api.esperas, [52.0, 52.0])
        self.assertAlmostEqual(self.estado()["requisicoes"]["esperado_pelo_ritmo_s"], 104.0)

        ritmo = self.modulo.Ritmo(por_janela=3, janela_s=10.0, relogio=api.relogio, espera=api.espera)
        api.esperas.clear()
        for _ in range(3):
            ritmo.antes()
        self.assertEqual(ritmo.pausa_pendente(), 10.0)
        ritmo.antes()
        self.assertEqual(api.esperas, [10.0])
        self.assertEqual(ritmo.pausa_pendente(), 0.0)

    def test_throttle_host_recua_a_janela_e_repete_o_item(self):
        api = ApiFalsa(estrangula_em={3})
        codigo, saida = self.roda(["--so", "urlinfo", "--max-requisicoes", "6"], api)
        self.assertEqual(codigo, 0)
        self.assertIn("THROTTLE urlinfo", saida)
        self.assertNotIn("FALHA", saida)
        # 6 requisicoes contadas: 5 aceitas + a estrangulada; o item foi repetido.
        self.assertEqual(len(api.chamadas), 6)
        urls = [p["url"] for _, p in api.chamadas]
        self.assertEqual(urls[2], urls[3], "o item estrangulado e repetido")
        self.assertEqual(api.esperas, [62.0], "recua a janela inteira")
        self.assertEqual(self.estado()["urlinfo"]["feitas"], 5)
        self.assertEqual(len(self.linhas("url_info")), 5)

        # Estrangulada duas vezes seguidas: o laco para e o cursor nao avanca sobre ela.
        api = ApiFalsa(estrangula_em={3, 4})
        codigo, saida = self.roda(["--so", "urlinfo", "--max-requisicoes", "6"], api, agora=DIA + dt.timedelta(days=1))
        self.assertEqual(codigo, 0)
        self.assertIn("API estrangulando mesmo apos recuo", saida)
        self.assertEqual(self.estado()["urlinfo"]["feitas"], 2)

    def test_tempo_maximo_corta_e_o_cursor_retoma(self):
        # Padrao de 100 s: 10 chamadas (10 s) + espera de 52 s + 10 chamadas
        # = 72 s; a 21a exigiria esperar ate 124 s e e cortada.
        api = ApiFalsa()
        codigo, saida = self.roda(["--so", "urlinfo"], api, tempo_maximo="padrao")
        self.assertEqual(codigo, 0)
        self.assertIn("cortado pelo tempo", saida)
        self.assertEqual(len(api.chamadas), 20)
        self.assertEqual(self.estado()["urlinfo"]["feitas"], 20)
        self.assertEqual(self.estado()["requisicoes"]["tempo_maximo_s"], 100.0)

        api2 = ApiFalsa()
        codigo, _ = self.roda(["--so", "urlinfo"], api2, tempo_maximo=3000)
        self.assertEqual(codigo, 0)
        self.assertEqual(len(api2.chamadas), 180, "retoma da 21a e conclui a janela")
        self.assertTrue(self.estado()["urlinfo"]["concluida"])


class TestExecucao(Base):
    def test_urlinfo_grava_linha_por_url_com_schema_tipo_e_coletado_em(self):
        api = ApiFalsa(paginas_rastreadas={BASE + self.paths[0]})
        codigo, _ = self.roda(["--so", "urlinfo"], api)
        self.assertEqual(codigo, 0)
        self.assertEqual(sum(1 for e, _ in api.chamadas if e == "GetUrlInfo"), 200)
        linhas = self.linhas("url_info")
        self.assertEqual(len(linhas), 200)
        for l in linhas:
            self.assertEqual(l["schema"], "bing_webmaster_v1")
            self.assertEqual(l["coletado_em"], DIA.isoformat())
            self.assertNotIn("__type", l)
            self.assertIn("Url", l)
            self.assertIn("LastCrawledDate", l)
        nunca = [l for l in linhas if l["LastCrawledDate"] is None]
        self.assertGreaterEqual(len(nunca), 199)
        estado = self.estado()
        self.assertEqual(estado["urlinfo"]["feitas"], 200)
        self.assertTrue(estado["urlinfo"]["concluida"])
        self.assertEqual((estado["requisicoes"]["teto"], estado["requisicoes"]["usadas"]), (400, 200))

        # Segunda execucao no mesmo dia: janela concluida, zero requisicoes.
        api2 = ApiFalsa()
        codigo, _ = self.roda(["--so", "urlinfo"], api2)
        self.assertEqual(codigo, 0)
        self.assertEqual(api2.chamadas, [])
        self.assertEqual(len(self.linhas("url_info")), 200, "nada regravado")

    def test_teto_corta_e_o_cursor_retoma_no_mesmo_dia(self):
        api = ApiFalsa()
        codigo, saida = self.roda(["--so", "urlinfo", "--max-requisicoes", "20"], api)
        self.assertEqual(codigo, 0)
        self.assertEqual(len(api.chamadas), 20, "o teto vale para a soma das chamadas")
        self.assertIn("cortado pelo teto", saida)
        estado = self.estado()
        self.assertEqual(estado["urlinfo"]["feitas"], 20)
        self.assertFalse(estado["urlinfo"]["concluida"])
        self.assertEqual((estado["requisicoes"]["teto"], estado["requisicoes"]["usadas"]), (20, 20))
        primeiras = [p["url"] for e, p in api.chamadas]

        api2 = ApiFalsa()
        self.roda(["--so", "urlinfo", "--max-requisicoes", "30"], api2)
        seguintes = [p["url"] for e, p in api2.chamadas]
        self.assertEqual(len(seguintes), 30)
        self.assertFalse(set(primeiras) & set(seguintes), "retoma de onde parou, nao repete")
        self.assertEqual(self.estado()["urlinfo"]["feitas"], 50)
        self.assertEqual(len(self.linhas("url_info")), 50)

        # Dia seguinte: janela nova, comeca do zero.
        api3 = ApiFalsa()
        self.roda(["--so", "urlinfo", "--max-requisicoes", "5"], api3, agora=DIA + dt.timedelta(days=1))
        self.assertEqual(self.estado()["urlinfo"]["feitas"], 5)
        self.assertEqual(self.estado()["urlinfo"]["dia"], "2026-09-10")

    def test_teto_e_compartilhado_entre_blocos_de_site_e_enriquecimento(self):
        api = ApiFalsa()
        codigo, saida = self.roda(["--max-requisicoes", "8"], api)
        self.assertEqual(codigo, 0)
        self.assertEqual(len(api.chamadas), 8)
        endpoints = [e for e, _ in api.chamadas]
        # 5 de site, depois 3 de GetUrlInfo; consulta_pagina reaproveita o
        # GetQueryStats do cache e nao paga de novo — mas nao sobra teto.
        self.assertEqual(endpoints[:5], ["GetRankAndTrafficStats", "GetCrawlStats", "GetQueryStats",
                                         "GetPageStats", "GetCrawlIssues"])
        self.assertEqual(endpoints[5:], ["GetUrlInfo"] * 3)
        estado = self.estado()
        self.assertEqual(estado["urlinfo"]["feitas"], 3)
        self.assertEqual(estado["enriquecimento"]["consulta_pagina"]["feitas"], [])
        self.assertIn("cortado pelo teto", estado["blocos"]["consulta_pagina"])

    def test_consulta_pagina_e_pagina_consulta_usam_o_topo_e_rotulam_os_dois_lados(self):
        api = ApiFalsa()
        codigo, _ = self.roda(["--so", "consulta_pagina"], api)
        self.assertEqual(codigo, 0)
        endpoints = [e for e, _ in api.chamadas]
        self.assertEqual(endpoints, ["GetQueryStats"] + ["GetQueryPageStats"] * 3)
        consultas = [p["query"] for e, p in api.chamadas if e == "GetQueryPageStats"]
        self.assertEqual(consultas, ["pensao alimenticia", "wiki juridica", "aviso previo"])
        linhas = self.linhas("consulta_pagina")
        self.assertEqual(len(linhas), 3)
        self.assertEqual(linhas[0]["Consulta"], "pensao alimenticia")
        self.assertEqual(linhas[0]["Pagina"], f"{BASE}/familia/pensao/")
        self.assertEqual(linhas[0]["Date"], "2026-09-04")
        estado = self.estado()["enriquecimento"]["consulta_pagina"]
        self.assertTrue(estado["concluido"])
        self.assertEqual(sorted(estado["feitas"]), sorted(consultas))

        api2 = ApiFalsa()
        codigo, _ = self.roda(["--so", "pagina_consulta"], api2)
        self.assertEqual(codigo, 0)
        self.assertEqual([e for e, _ in api2.chamadas], ["GetPageStats"] + ["GetPageQueryStats"] * 2)
        paginas = [p["page"] for e, p in api2.chamadas if e == "GetPageQueryStats"]
        self.assertEqual(paginas, [f"{BASE}/familia/pensao/", f"{BASE}/"])
        linhas = self.linhas("pagina_consulta")
        self.assertEqual(len(linhas), 2)
        self.assertEqual(linhas[0]["Pagina"], f"{BASE}/familia/pensao/")
        self.assertEqual(linhas[0]["Consulta"], "pensao alimenticia")

        # Mesmo dia de novo: so a chamada de base; as chaves ja feitas nao se repetem.
        api3 = ApiFalsa()
        self.roda(["--so", "pagina_consulta"], api3)
        self.assertEqual([e for e, _ in api3.chamadas], ["GetPageStats"])
        self.assertEqual(len(self.linhas("pagina_consulta")), 2)

    def test_falhas_seguidas_param_o_laco_sem_avancar_o_cursor(self):
        api = ApiFalsa(derruba={"GetUrlInfo": 3})

        # Deixa a 3a, 4a e 5a chamadas falharem: derruba e por indice, entao
        # embrulha para falhar tres vezes seguidas.
        class Api3(ApiFalsa):
            def __call__(self, url):
                partes = urllib.parse.urlsplit(url)
                if partes.path.endswith("GetUrlInfo"):
                    vez = sum(1 for e, _ in self.chamadas if e == "GetUrlInfo") + 1
                    if vez in (3, 4, 5):
                        self.chamadas.append(("GetUrlInfo", dict(urllib.parse.parse_qsl(partes.query))))
                        raise urllib.error.HTTPError(url, 500, "fora", {}, io.BytesIO(b""))
                return ApiFalsa.__call__(self, url)

        api = Api3()
        codigo, saida = self.roda(["--so", "urlinfo"], api)
        self.assertEqual(codigo, 0, "duas consultas foram gravadas: nao e API inteira fora")
        self.assertEqual(len(api.chamadas), 5)
        self.assertIn("3 falhas seguidas", saida)
        self.assertEqual(self.estado()["urlinfo"]["feitas"], 2, "so o que respondeu avanca")
        self.assertEqual(len(self.linhas("url_info")), 2)

    def test_cada_bloco_descarrega_no_ledger_antes_do_seguinte(self):
        class MorreNoPageQueryStats(ApiFalsa):
            """Morre na 1a chamada do ULTIMO bloco (pagina_consulta), como um
            SIGTERM no minuto 30 do run noturno; RuntimeError nao e erro de
            rede e atravessa o coletor."""

            def __call__(self, url):
                if url.split("?")[0].endswith("GetPageQueryStats"):
                    raise RuntimeError("processo morto no meio do run")
                return ApiFalsa.__call__(self, url)

        api = MorreNoPageQueryStats()
        with self.assertRaises(RuntimeError):
            self.roda([], api)
        # Tudo que veio ANTES do bloco que morreu ja esta no disco.
        self.assertEqual(len(self.linhas("busca_diaria")), 1)
        self.assertEqual(len(self.linhas("consulta_diaria")), 4)
        self.assertEqual(len(self.linhas("url_info")), 200)
        self.assertEqual(len(self.linhas("consulta_pagina")), 3)
        self.assertEqual(len(self.linhas("pagina_consulta")), 0)
        estado = self.estado()
        self.assertEqual(estado["urlinfo"]["feitas"], 200)
        self.assertTrue(estado["enriquecimento"]["consulta_pagina"]["concluido"])
        self.assertNotIn("pagina_consulta", estado["enriquecimento"])
        self.assertEqual(estado["linhas_novas"], 1 + 1 + 4 + 2 + 200 + 3)

    def test_sem_credencial_sai_2_e_api_inteira_fora_sai_2(self):
        os.environ.pop(self.modulo.CHAVE, None)
        codigo, saida = self.roda(["--so", "trafego"], ApiFalsa())
        self.assertEqual(codigo, 2)
        self.assertIn("sem credencial", saida)
        self.assertFalse(self.modulo.SERIE.exists())

        os.environ[self.modulo.CHAVE] = "chave-de-teste"

        def fora(url):
            raise urllib.error.URLError("rede fora")

        codigo, _ = self.roda(["--so", "trafego"], fora)
        self.assertEqual(codigo, 2)
        codigo, _ = self.roda([], fora)
        self.assertEqual(codigo, 2, "todos os blocos pedidos falharam")

    def test_falha_parcial_sai_1_e_grava_o_que_veio(self):
        api = ApiFalsa(derruba={"GetCrawlStats": 1})
        codigo, saida = self.roda(["--so", "rastreio"], api)
        self.assertEqual(codigo, 2, "um bloco pedido, um bloco falhou")
        api = ApiFalsa(derruba={"GetCrawlStats": 1})
        codigo, saida = self.roda([], api)
        self.assertEqual(codigo, 1)
        self.assertIn("FALHA rastreio", saida)
        self.assertGreater(len(self.linhas("busca_diaria")), 0)
        self.assertEqual(self.estado()["blocos"]["rastreio"], "erro 500")

    def test_linha_identica_nao_regrava_e_o_cursor_preserva_blocos_de_outras_execucoes(self):
        api = ApiFalsa()
        self.roda(["--so", "trafego"], api)
        self.assertEqual(len(self.linhas("busca_diaria")), 1)
        self.roda(["--so", "trafego"], ApiFalsa(), agora=DIA + dt.timedelta(hours=6))
        self.assertEqual(len(self.linhas("busca_diaria")), 1, "identica: nao regrava")
        self.roda(["--so", "rastreio"], ApiFalsa())
        blocos = self.estado()["blocos"]
        self.assertIn("trafego", blocos)
        self.assertIn("rastreio", blocos)


class IdentidadeDeSaida(unittest.TestCase):
    """O UNICO teste que exercita `busca_json`, o caminho real de rede.

    Os demais testes deste arquivo injetam `busca`, e por isso nunca viram um
    cabecalho: foi por esse buraco que a ferramenta saiu como `Python-urllib/3.x`
    para ssl.bing.com desde a primeira coleta da serie (`min(coletado_em)` em
    data/ops/bing_webmaster_daily.jsonl = 2026-08-29T06:00:00Z) ate 2026-09-10,
    sem nenhum gate acusar. Aqui a rede e'
    dublada UM NIVEL ABAIXO — em `urllib.request.urlopen` — para que o
    `Request` montado pela ferramenta possa ser lido.

    PROVA POR MUTACAO: apagar `"User-Agent": USER_AGENT` de `busca_json` deixa
    este teste vermelho. Para ver sem tocar na ferramenta:

      cp tools/collect-bing-webmaster /tmp/x && sed -i 's/, "User-Agent": USER_AGENT//' /tmp/x
      WIKI_BING_COLETOR_ALVO=/tmp/x python3 tools/test_collect_bing_webmaster.py
    """

    CANONICO = re.compile(
        r"^Mozilla/5\.0 \(compatible; WikijuridicaBot/\d+\.\d+; "
        r"\+https://wikijuridica\.com\.br/bot/; [a-z0-9][a-z0-9 .,:/-]*\)$")

    def setUp(self):
        self.modulo = _carrega_modulo_fresco()

    @contextlib.contextmanager
    def _urlopen_dublado(self, corpo=b'{"d": []}'):
        """Substitui `urlopen` no urllib que o MODULO importou e devolve a
        lista de requisicoes que ele tentou fazer. Nada sai da maquina."""
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
            return RespostaFalsa(corpo)

        original = self.modulo.urllib.request.urlopen
        self.modulo.urllib.request.urlopen = falso_urlopen
        try:
            yield capturadas
        finally:
            self.modulo.urllib.request.urlopen = original

    def test_busca_json_sai_como_wikijuridicabot(self):
        with self._urlopen_dublado() as pedidos:
            self.modulo.busca_json("https://ssl.bing.com/webmaster/api.svc/json/GetQueryStats")
        self.assertEqual(len(pedidos), 1)
        # urllib normaliza o nome do cabecalho para "User-agent".
        enviado = pedidos[0].get_header("User-agent")
        self.assertIsNotNone(enviado, "a requisicao saiu sem User-Agent: o urllib mandaria Python-urllib")
        self.assertNotIn("Python-urllib", enviado)
        self.assertRegex(enviado, self.CANONICO)

    def test_proposito_declara_leitura_de_metadado(self):
        """O proposito nao e' decorativo: ele diz ao operador do outro lado o
        que a coleta faz. Este bloco LE metadado publico de demanda."""
        self.assertTrue(self.modulo.USER_AGENT.endswith("; observacao-de-demanda)"),
                        self.modulo.USER_AGENT)

    def test_nao_se_apresenta_como_navegador_nem_como_bot_de_terceiro(self):
        ua = self.modulo.USER_AGENT
        for proibido in ("Chrome/", "Safari/", "Firefox/", "Edg/",
                         "Googlebot", "bingbot", "GPTBot", "ClaudeBot"):
            self.assertNotIn(proibido, ua)


if __name__ == "__main__":
    unittest.main()
