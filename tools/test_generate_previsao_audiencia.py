#!/usr/bin/env python3
"""Testes de tools/generate-previsao-audiencia — fixtures sintéticas numa raiz
temporária, nunca os ledgers reais (o run-qualidade-diaria envelopa cada teste
em timeout de 180 s; esta bancada roda em ~1 s).

O que estes testes travam — e, em cada asserção, qual linha do gerador a faz
reprovar quando removida (a anotação está ao lado da asserção):
  - taxa semanal recuperada de série sintética (+2 %/semana, sábado e domingo
    a −30 %) dentro de ±0,5 p.p., e o valor VERDADEIRO (sem ruído) a 30 e a
    180 dias dentro do IC80;
  - série curta → sem_serie_suficiente; série com ≥ 50 % de zeros → serie_esparsa;
  - dia provisório FORA do ajuste, provado por MUTAÇÃO do guarda (o mutante
    inclui o dia e o número muda);
  - dia ausente é ausente, não zero;
  - a borda dos bots entra pela série saneada (última linha por (date,
    agent_key), linha impossível descartada), nunca pela soma do JSONL cru;
  - ranking de áreas: bot valioso × scanner × simulação × aquecimento × 301 ×
    404 × fora do acervo, área do tema em /redesocial/tema/<área>/, páginas
    publicadas por área (noindex fora), fator = 1 + taxa de bots.total;
  - o leitor de content/pages.json por blocos dá o mesmo resultado com bloco
    minúsculo (fronteira de bloco no meio do objeto);
  - --gravar × sem: nada toca o disco sem a flag; linha idêntica à última
    (fora gerado_em) não se regrava; janela diferente grava linha nova;
  - determinismo: duas execuções com o mesmo `agora` dão o mesmo JSON.
"""
import contextlib
import datetime as dt
import importlib.util
import io
import json
import math
import os
import random
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FERRAMENTA = os.path.join(RAIZ, "tools", "generate-previsao-audiencia")
HOJE = "2026-09-09"
ONTEM = "2026-09-08"
D_HOJE = dt.date.fromisoformat(HOJE)
D_ONTEM = dt.date.fromisoformat(ONTEM)
AGORA = "2026-09-09T07:10:00+00:00"
DIAS_SERIE = 70
INICIO_SERIE = D_ONTEM - dt.timedelta(days=DIAS_SERIE - 1)
LACUNAS = ("2026-08-20", "2026-08-21")
PRESO_PROVISORIO = "2026-08-01"   # como o 2026-08-13 real: basis provisional_ e nunca fechou
FDS = 0.7


def carrega_modulo(nome="generate_previsao_audiencia", fonte=None):
    """Carrega a ferramenta (sem extensão .py). Com `fonte`, executa ESSE texto
    no lugar do arquivo — é assim que o mutante nasce."""
    loader = SourceFileLoader(nome, FERRAMENTA)
    spec = importlib.util.spec_from_loader(nome, loader)
    modulo = importlib.util.module_from_spec(spec)
    if fonte is None:
        loader.exec_module(modulo)
    else:
        modulo.__file__ = FERRAMENTA
        exec(compile(fonte, FERRAMENTA, "exec"), modulo.__dict__)
    return modulo


def sintetica(base, taxa_semanal, sigma, semente, fds=FDS):
    """Série diária de DIAS_SERIE dias terminando ONTEM: base·e^(b·i)·fds(dia),
    com ruído lognormal de desvio `sigma` e semente fixa. Devolve (pontos, b)."""
    rnd = random.Random(semente)
    b = math.log1p(taxa_semanal) / 7.0
    pontos = {}
    for i in range(DIAS_SERIE):
        d = INICIO_SERIE + dt.timedelta(days=i)
        media = base * math.exp(b * i) * (fds if d.weekday() >= 5 else 1.0)
        pontos[d.isoformat()] = int(round(media * math.exp(rnd.gauss(0.0, sigma))))
    return pontos, b


def verdade_em(base, b, data, fds=FDS):
    i = (data - INICIO_SERIE).days
    return base * math.exp(b * i) * (fds if data.weekday() >= 5 else 1.0)


ORGANIC, B_ORGANIC = sintetica(5000, 0.02, 0.03, 7)
UNIQUES, B_UNIQUES = sintetica(800, -0.01, 0.03, 11)
OAI, B_OAI = sintetica(300, 0.03, 0.03, 3)
BINGBOT, B_BINGBOT = sintetica(200, 0.0, 0.03, 5)
IMPRESSOES, B_IMPRESSOES = sintetica(100, 0.05, 0.03, 13)
RASTREIO, B_RASTREIO = sintetica(50, 0.01, 0.05, 17)
SEMRUSH = 2000


def escreve_jsonl(caminho, linhas):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as handle:
        for linha in linhas:
            handle.write(json.dumps(linha, ensure_ascii=False) + "\n")


def linha_bot(d, agente, valor, funcao="search"):
    # v1: os dois contadores, sem pernas de verificação — a série saneada aceita
    # (estimado ≥ amostrado, fator 1) e não exige a soma do v4.
    return {"date": d, "agent_key": agente, "function": funcao, "requests_estimated": valor,
            "requests_sampled": valor, "schema_version": "edge_bot_agents_daily_v1"}


def linha_nginx(dia, agente, path, route_class="page", status=200, bot_simulation=False, warming=False, ts=None):
    return {"ts": ts or (dia + "T10:00:00Z"), "agent_key": agente, "path": path, "route_class": route_class,
            "status": status, "bot_simulation": bot_simulation, "warming": warming,
            "schema_version": "origin_access_nginx_v2"}


def monta_fixture(raiz):
    ops = os.path.join(raiz, "data", "ops")
    # --- borda: uma linha por dia, lacunas, um dia preso em provisional_ e o dia em curso
    borda = []
    for d in sorted(ORGANIC):
        if d in LACUNAS:
            continue
        linha = {"date": d, "requests": ORGANIC[d] + 100, "self_warming_requests": 100,
                 "organic_requests": ORGANIC[d], "page_views": ORGANIC[d] // 2, "uniques": UNIQUES[d],
                 "organic_requests_basis": "exact_raw_minus_warming_ledger", "self_warming_note": "",
                 "schema_version": "edge_traffic_daily_v5"}
        if d == PRESO_PROVISORIO:
            linha["organic_requests"] = ORGANIC[d] * 10
            linha["organic_requests_basis"] = "provisional_raw_minus_warming_ledger"
            linha["self_warming_note"] = "dia em curso: bruto e aquecimento ainda crescendo"
        if d == ONTEM:
            # última linha por date vence: a primeira é um snapshot velho
            borda.append(dict(linha, organic_requests=1, uniques=1))
        borda.append(linha)
    borda.append({"date": HOJE, "requests": 999999, "self_warming_requests": 0, "organic_requests": 999999,
                  "page_views": 1, "uniques": 999999, "organic_requests_basis": "provisional_raw_minus_warming_ledger",
                  "self_warming_note": "dia em curso: bruto e aquecimento ainda crescendo",
                  "schema_version": "edge_traffic_daily_v5"})
    escreve_jsonl(os.path.join(ops, "edge_traffic_daily.jsonl"), borda)

    # --- bots: saneada = última linha por (date, agent_key), linha impossível descartada
    bots = []
    for d in sorted(OAI):
        if d == ONTEM:
            bots.append(linha_bot(d, "oai-searchbot", 1))          # snapshot velho, perde para o último
        bots.append(linha_bot(d, "oai-searchbot", OAI[d]))
        bots.append(linha_bot(d, "bingbot", BINGBOT[d]))
        bots.append(linha_bot(d, "semrushbot", SEMRUSH, "seo"))
    # linha fisicamente impossível (estimado < amostrado) como ÚLTIMA do bingbot em ONTEM:
    # a saneada a descarta e a válida anterior fica
    bots.append({"date": ONTEM, "agent_key": "bingbot", "function": "search", "requests_estimated": 10,
                 "requests_sampled": 999999, "schema_version": "edge_bot_agents_daily_v1"})
    for i in range(30):                                            # 30 dias, 16 zeros → esparsa
        d = (D_ONTEM - dt.timedelta(days=29 - i)).isoformat()
        bots.append(linha_bot(d, "claude-user", 0 if i < 16 else 5, "user"))
    for i in range(5):                                             # 5 dias → curta
        d = (D_ONTEM - dt.timedelta(days=4 - i)).isoformat()
        bots.append(linha_bot(d, "perplexity-user", 1, "user"))
    bots.append(linha_bot(HOJE, "oai-searchbot", 99999))            # dia em curso, cumulativo: fora
    escreve_jsonl(os.path.join(ops, "edge_bot_agents_daily.jsonl"), bots)

    # --- Bing: impressions 70 dias; clicks só nos últimos 15; InIndex crescente
    bing = []
    for i, d in enumerate(sorted(IMPRESSOES)):
        linha = {"tipo": "busca_diaria", "Date": d, "Impressions": str(IMPRESSOES[d])}
        if i >= DIAS_SERIE - 15:
            linha["Clicks"] = str(IMPRESSOES[d] // 20)
        bing.append(linha)
        bing.append({"tipo": "rastreio_diario", "Date": d, "InIndex": str(100 + 60 * i),
                     "CrawledPages": str(RASTREIO[d]), "Code5xx": "0"})
    escreve_jsonl(os.path.join(ops, "bing_webmaster_daily.jsonl"), bing)

    # --- origem: só 3 dos 14 dias têm ledger
    acesso = os.path.join(ops, "access")
    escreve_jsonl(os.path.join(acesso, "nginx-2026-09-08.jsonl"), [
        *[linha_nginx("2026-09-08", "oai-searchbot", "/trabalhista/a/") for _ in range(5)],
        *[linha_nginx("2026-09-08", "bingbot", "/familia/b", "outro", 301) for _ in range(3)],
        *[linha_nginx("2026-09-08", "bingbot", "/familia/b/") for _ in range(2)],
        *[linha_nginx("2026-09-08", "semrushbot", "/familia/b/") for _ in range(10)],
        *[linha_nginx("2026-09-08", "googlebot", "/familia/b/", bot_simulation=True) for _ in range(7)],
        *[linha_nginx("2026-09-08", "perplexitybot", "/trabalhista/a/", warming=True) for _ in range(3)],
        *[linha_nginx("2026-09-08", "oai-searchbot", "/trabalhista/zzz/", "not_found", 404) for _ in range(2)],
        linha_nginx("2026-09-08", "oai-searchbot", "/wp-json/x/"),
        linha_nginx("2026-09-08", "oai-searchbot", "/trabalhista/a/", ts="2026-09-05T10:00:00Z"),
        linha_nginx("2026-09-08", "chatgpt-user", "/mcp", "mcp", 200),
    ])
    escreve_jsonl(os.path.join(acesso, "nginx-2026-09-07.jsonl"), [
        *[linha_nginx("2026-09-07", "oai-searchbot", "/trabalhista/a/index.md", "markdown") for _ in range(2)],
        linha_nginx("2026-09-07", "amazonbot", "/consumidor/c1/", status=304),
    ])
    escreve_jsonl(os.path.join(acesso, "nginx-2026-09-06.jsonl"), [
        linha_nginx("2026-09-06", "chatgpt-user", "/redesocial/tema/consumidor/x/"),
    ])
    # fora da janela de 14 dias: não conta
    escreve_jsonl(os.path.join(acesso, "nginx-2026-08-25.jsonl"), [
        *[linha_nginx("2026-08-25", "oai-searchbot", "/familia/b/") for _ in range(50)],
    ])

    # --- acervo: 8 publicadas em 4 áreas; a noindex não conta
    paginas = [
        {"path": "/", "status": "published", "title": "Início"},
        {"path": "/trabalhista/a/", "status": "published", "title": "Página A"},
        {"path": "/trabalhista/b/", "status": "published", "title": "Página B"},
        {"path": "/trabalhista/c/", "status": "noindex", "title": "Página C"},
        {"path": "/familia/b/", "status": "published", "title": "Página B da família"},
    ] + [{"path": "/consumidor/c%d/" % i, "status": "published", "title": "Consumidor %d — acentuação" % i}
         for i in range(1, 5)]
    os.makedirs(os.path.join(raiz, "content"), exist_ok=True)
    with open(os.path.join(raiz, "content", "pages.json"), "w", encoding="utf-8") as handle:
        json.dump(paginas, handle, ensure_ascii=False, indent=2)


class Calculo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.modulo = carrega_modulo()
        cls.temporario = tempfile.TemporaryDirectory(prefix="previsao-fixture-")
        cls.raiz = cls.temporario.name
        monta_fixture(cls.raiz)
        cls.obj = cls.modulo.calcula(cls.raiz, D_HOJE, 60, agora=AGORA)

    @classmethod
    def tearDownClass(cls):
        cls.temporario.cleanup()

    def serie(self, nome):
        return self.obj["series"][nome]

    def test_taxa_recuperada_e_verdade_dentro_do_ic80(self):
        s = self.serie("borda.organic_requests")
        # reprova se: `taxa()` deixar de multiplicar b por 7, ou `linha_x` perder os dummies
        # (o −30 % de fim de semana vira erro de tendência e a taxa sai do ±0,5 p.p.)
        self.assertAlmostEqual(s["taxa_semanal_pct"], 2.0, delta=0.5, msg=s)
        self.assertLess(s["ic80"][0], 2.0)
        self.assertGreater(s["ic80"][1], 2.0)
        self.assertGreater(s["r2"], 0.9)
        for h in ("30", "180"):
            pv = s["previsao"][h]
            # reprova se: `data = ultimo + timedelta(days=h)` usar hoje em vez do último dia ajustado
            self.assertEqual(pv["data"], (D_ONTEM + dt.timedelta(days=int(h))).isoformat())
            verdade = verdade_em(5000, B_ORGANIC, dt.date.fromisoformat(pv["data"]))
            # reprova se: `se_pred` perder o termo `1 +` (IC do valor médio, não de previsão) ou
            # `x0` for montado sem o dummy do dia-alvo (o 180.º dia cai num domingo, a −30 %)
            self.assertLessEqual(pv["ic80"][0], verdade, (h, pv, verdade))
            self.assertGreaterEqual(pv["ic80"][1], verdade, (h, pv, verdade))
            self.assertLess(pv["ic80"][0], pv["ponto"])
            self.assertLess(pv["ponto"], pv["ic80"][1])
            self.assertLess(pv["ic95"][0], pv["ic80"][0])
            self.assertGreater(pv["ic95"][1], pv["ic80"][1])
        # reprova se: `acumulado` deixar de somar os pontos diários de 1..h (inclusive os
        # fins de semana a −30 %): a soma verdadeira dos 30 dias seguintes fica a menos de 5 %
        soma_verdadeira = sum(verdade_em(5000, B_ORGANIC, D_ONTEM + dt.timedelta(days=k)) for k in range(1, 31))
        self.assertAlmostEqual(s["previsao"]["30"]["acumulado"] / soma_verdadeira, 1.0, delta=0.05,
                               msg=(s["previsao"]["30"], soma_verdadeira))
        self.assertGreater(s["previsao"]["90"]["acumulado"], s["previsao"]["30"]["acumulado"])
        oai = self.serie("bots.oai-searchbot")
        self.assertAlmostEqual(oai["taxa_semanal_pct"], 3.0, delta=0.5, msg=oai)
        uniq = self.serie("borda.uniques")
        self.assertAlmostEqual(uniq["taxa_semanal_pct"], -1.0, delta=0.5, msg=uniq)

    def test_serie_curta_e_serie_esparsa_nao_projetam(self):
        curta = self.serie("bots.perplexity-user")
        # reprova se: `if n < MINIMO_DIAS` for removido
        self.assertEqual((curta["motivo"], curta["n"], curta["previsao"], curta["taxa_semanal_pct"]),
                         ("sem_serie_suficiente", 5, None, None))
        self.assertIn("mínimo 21", curta["detalhe"])
        esparsa = self.serie("bots.claude-user")
        # reprova se: `if zeros / n >= FRACAO_ZEROS_ESPARSA` for removido
        self.assertEqual((esparsa["motivo"], esparsa["n"], esparsa["zeros"], esparsa["previsao"]),
                         ("serie_esparsa", 30, 16, None))
        self.assertEqual(esparsa["ultimo_valor"], 5, "esparsa RELATA o último valor")
        clicks = self.serie("bing.clicks")
        # reprova se: `numero(r.get("Clicks"))` virar 0 quando o campo falta (ausente ≠ zero)
        self.assertEqual((clicks["motivo"], clicks["n"]), ("sem_serie_suficiente", 15))
        self.assertIsNone(self.serie("bing.impressions")["motivo"])

    def test_dia_ausente_e_ausente_nao_zero(self):
        s = self.serie("borda.organic_requests")
        # janela 07-12→09-09: 59 dias com data ≤ ontem, −2 lacunas, −1 preso em provisional_
        # reprova se: um dia sem linha entrar como 0 (n subiria para 58 e zeros para 2)
        self.assertEqual((s["n"], s["zeros"]), (56, 0))
        self.assertEqual(self.serie("borda.uniques")["n"], 56)
        self.assertEqual(s["primeiro_dia"], "2026-07-12")
        self.assertEqual(s["ultimo_dia"], ONTEM)
        # reprova se: `ultima_por_chave` não fizer a última linha por date vencer
        self.assertEqual(s["ultimo_valor"], ORGANIC[ONTEM])

    def test_provisorio_fora_do_ajuste_provado_por_mutacao(self):
        original = self.serie("borda.organic_requests")
        # reprova se: `provisorio_borda` deixar de ler `organic_requests_basis`/`self_warming_note`
        self.assertEqual(original["dias_provisorios_excluidos"], [PRESO_PROVISORIO, HOJE])
        self.assertNotIn(HOJE, [original["ultimo_dia"]])
        with open(FERRAMENTA, encoding="utf-8") as handle:
            fonte = handle.read()
        guarda = "and d not in provisorios]"
        self.assertEqual(fonte.count(guarda), 1, "o guarda mutável precisa existir uma única vez")
        mutante = carrega_modulo("generate_previsao_audiencia_mutante", fonte.replace(guarda, "]"))
        mutado = mutante.calcula(self.raiz, D_HOJE, 60, agora=AGORA)["series"]["borda.organic_requests"]
        print("\n  mutante vermelho: original n=%d taxa=%s | mutante(sem guarda) n=%d taxa=%s"
              % (original["n"], original["taxa_semanal_pct"], mutado["n"], mutado["taxa_semanal_pct"]))
        # reprova se: o guarda `d not in provisorios` for removido do gerador real
        self.assertEqual(mutado["n"], original["n"] + 2)
        self.assertNotEqual(mutado["taxa_semanal_pct"], original["taxa_semanal_pct"])
        self.assertEqual(mutado["ultimo_dia"], HOJE)
        # o dia em curso dos bots também fica fora (ledger cumulativo)
        oai = self.serie("bots.oai-searchbot")
        self.assertEqual(oai["ultimo_dia"], ONTEM)
        self.assertEqual(oai["dias_provisorios_excluidos"], [HOJE])

    def test_bots_pela_serie_saneada_nunca_pela_soma_crua(self):
        oai = self.serie("bots.oai-searchbot")
        # reprova se: o gerador somar as linhas cruas do dia (daria 1 + OAI[ONTEM])
        self.assertEqual(oai["ultimo_valor"], OAI[ONTEM])
        bing = self.serie("bots.bingbot")
        # reprova se: a linha impossível (estimado < amostrado) entrar — ou seja, se a
        # leitura deixar de passar por edgetelemetry.serie_saneada
        self.assertEqual(bing["ultimo_valor"], BINGBOT[ONTEM])
        self.assertAlmostEqual(bing["taxa_semanal_pct"], 0.0, delta=0.5, msg=bing)
        total = self.serie("bots.total")
        valiosos = self.serie("bots.valiosos")
        # reprova se: bots.total deixar de somar o agente não valioso (semrushbot) ou
        # bots.valiosos passar a somá-lo
        self.assertEqual(total["ultimo_valor"], OAI[ONTEM] + BINGBOT[ONTEM] + SEMRUSH + 5 + 1)
        self.assertEqual(valiosos["ultimo_valor"], OAI[ONTEM] + BINGBOT[ONTEM] + 5 + 1)
        self.assertEqual(total["n"], DIAS_SERIE - 11)   # janela de 60 termina hoje: 59 dias ≤ ontem
        self.assertIn("serie_saneada", " ".join(self.obj["ressalvas"]))

    def test_ranking_de_areas(self):
        areas = {a["area"]: a for a in self.obj["areas"]}
        meta = self.obj["areas_meta"]
        self.assertEqual([a["area"] for a in self.obj["areas"]], ["trabalhista", "consumidor", "familia", "(raiz)"])
        # reprova se: route_class 'outro'/'not_found'/'mcp' ou status 301/404 entrarem, ou se
        # bot_simulation/warming deixarem de ser filtrados, ou se semrushbot contar
        self.assertEqual(areas["trabalhista"]["por_agente"], {"oai-searchbot": 7})
        self.assertEqual(areas["familia"]["por_agente"], {"bingbot": 2})
        # reprova se: `area_de` não mapear /redesocial/tema/<área>/, ou se 304 deixar de contar
        self.assertEqual(areas["consumidor"]["por_agente"], {"amazonbot": 1, "chatgpt-user": 1})
        self.assertEqual(areas["(raiz)"]["leituras_14d"], 0)
        # reprova se: a página noindex contar como publicada
        self.assertEqual([areas[a]["paginas_publicadas"] for a in ("trabalhista", "familia", "consumidor", "(raiz)")],
                         [2, 1, 4, 1])
        self.assertEqual(areas["trabalhista"]["leituras_por_pagina"], 3.5)
        self.assertEqual(areas["consumidor"]["leituras_por_pagina"], 0.5)
        taxa_total = self.serie("bots.total")["taxa_semanal_pct"]
        # reprova se: o fator deixar de vir de bots.total
        self.assertEqual(meta["fator_serie"], "bots.total")
        self.assertEqual(meta["fator"], round(1.0 + taxa_total / 100.0, 4))
        for a in self.obj["areas"]:
            self.assertEqual(a["valor_esperado"], round(a["leituras_14d"] * meta["fator"], 2), a)
        # reprova se: o ts de outro dia dentro do arquivo contar, ou se o path fora do acervo
        # cair no ranking em vez de fora_do_acervo
        self.assertEqual(meta["fora_do_acervo"], {"wp-json": 1})
        self.assertEqual(meta["leituras_total"], 11)
        self.assertEqual(meta["janela"], {"inicio": "2026-08-26", "fim": ONTEM, "dias": 14})
        self.assertEqual(len(meta["dias_sem_ledger"]), 11)
        self.assertEqual(meta["dias_com_ledger"], ["2026-09-06", "2026-09-07", "2026-09-08"])
        self.assertEqual(meta["linhas_descartadas_proprias"], 10)
        self.assertEqual(meta["paginas_publicadas_total"], 8)
        idx = self.serie("bing.indexadas")
        # reprova se: o teto físico deixar de ser o total de páginas publicadas
        self.assertEqual(idx["teto_fisico"], 8)
        self.assertTrue(all(idx["previsao"][h]["acima_do_teto"] for h in ("30", "90", "180")))
        ad = self.modulo.area_de
        self.assertEqual((ad("/"), ad(""), ad("/trabalhista/a/"), ad("/redesocial/tema/consumidor/x/"),
                          ad("/redesocial/area/consumidor/"), ad("/redesocial/tema/")),
                         ("(raiz)", "(raiz)", "trabalhista", "consumidor", "redesocial", "redesocial"))

    def test_leitor_de_pages_por_blocos(self):
        caminho = os.path.join(self.raiz, "content", "pages.json")
        esperado = {"(raiz)": 1, "trabalhista": 2, "familia": 1, "consumidor": 4}
        self.assertEqual(self.modulo.paginas_por_area(caminho), esperado)
        # reprova se: o laço `while True: try raw_decode / except: estende o buffer` for
        # simplificado para uma leitura inteira — com bloco de 7 caracteres toda fronteira cai
        # no meio de um objeto
        self.assertEqual(self.modulo.paginas_por_area(caminho, tamanho_bloco=7), esperado)
        self.assertEqual(self.modulo.paginas_por_area(caminho, tamanho_bloco=1), esperado)
        quebrado = os.path.join(self.raiz, "content", "quebrado.json")
        with open(quebrado, "w", encoding="utf-8") as handle:
            handle.write('[{"path": "/a/", "status": "published"}, {"path": "/b/"')
        with self.assertRaises(ValueError):
            self.modulo.paginas_por_area(quebrado, tamanho_bloco=7)

    def test_determinismo(self):
        de_novo = self.modulo.calcula(self.raiz, D_HOJE, 60, agora=AGORA)
        # reprova se: alguma saída depender de ordem de dict não determinística, de relógio
        # (`gerado_em` sem `agora`) ou de estado entre execuções
        self.assertEqual(json.dumps(self.obj, sort_keys=False), json.dumps(de_novo, sort_keys=False))
        self.assertEqual(self.obj["schema_version"], "previsao_v1")
        self.assertEqual(list(self.obj)[:5], ["schema_version", "date", "gerado_em", "janela_dias", "janela"])
        self.assertEqual(self.obj["gerado_em"], AGORA)
        self.assertEqual(self.obj["ultimo_dia_completo"], ONTEM)
        self.assertEqual(sorted(self.obj["series"]), sorted(
            ["borda.organic_requests", "borda.uniques", "bots.total", "bots.valiosos"] +
            ["bots." + a for a in self.modulo.AGENTES_VALIOSOS] +
            ["bing.impressions", "bing.clicks", "bing.rastreio", "bing.indexadas"]))


class Gravacao(unittest.TestCase):
    def setUp(self):
        self.modulo = carrega_modulo()
        self.temporario = tempfile.TemporaryDirectory(prefix="previsao-gravar-")
        self.raiz = self.temporario.name
        monta_fixture(self.raiz)
        self.jsonl = os.path.join(self.raiz, "data", "ops", "previsao_daily.jsonl")
        self.json = os.path.join(self.raiz, "data", "ops", "painel", "previsao.json")

    def tearDown(self):
        self.temporario.cleanup()

    def roda(self, *extra):
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            codigo = self.modulo.main(["--raiz", self.raiz, "--hoje", HOJE, *extra])
        return codigo, saida.getvalue()

    def linhas(self):
        if not os.path.isfile(self.jsonl):
            return []
        with open(self.jsonl, encoding="utf-8") as handle:
            return [json.loads(l) for l in handle if l.strip()]

    def test_sem_gravar_nada_toca_o_disco(self):
        codigo, saida = self.roda("--dry-run")
        self.assertEqual(codigo, 0)
        self.assertIn("sem --gravar", saida)
        self.assertIn("borda.organic_requests", saida)
        self.assertIn("trabalhista", saida)
        # reprova se: `if not args.gravar: return 0` for removido de main()
        self.assertFalse(os.path.exists(self.jsonl))
        self.assertFalse(os.path.exists(self.json))
        codigo, _ = self.roda()
        self.assertEqual(codigo, 0)
        self.assertFalse(os.path.exists(self.jsonl), "sem flag nenhuma, o padrão também é só imprimir")

    def test_gravar_escreve_os_dois_e_nao_regrava_linha_identica(self):
        codigo, saida = self.roda("--gravar")
        self.assertEqual(codigo, 0)
        self.assertIn("linha nova", saida)
        self.assertEqual(len(self.linhas()), 1)
        with open(self.json, encoding="utf-8") as handle:
            painel = json.load(handle)
        self.assertEqual(painel["schema_version"], "previsao_v1")
        self.assertEqual(painel["date"], HOJE)
        self.assertEqual(self.linhas()[0]["series"]["borda.organic_requests"]["n"], 56)
        antes = os.stat(self.json).st_mtime_ns
        codigo, saida = self.roda("--gravar")
        self.assertEqual(codigo, 0)
        # reprova se: `_sem_volateis(anterior) != _sem_volateis(objeto)` deixar de guardar o append
        self.assertEqual(len(self.linhas()), 1, "linha idêntica (fora gerado_em) não se regrava")
        self.assertIn("não regravada", saida)
        self.assertEqual(os.stat(self.json).st_mtime_ns, antes, "JSON inalterado não é reescrito")
        codigo, _ = self.roda("--gravar", "--dias", "40")
        self.assertEqual(codigo, 0)
        # reprova se: a janela deixar de fazer parte do objeto comparado
        self.assertEqual(len(self.linhas()), 2)
        self.assertEqual(self.linhas()[-1]["janela_dias"], 40)
        with open(self.json, encoding="utf-8") as handle:
            self.assertEqual(json.load(handle)["janela_dias"], 40, "previsao.json é sempre o último objeto")

    def test_raiz_inexistente_e_instrumento_quebrado(self):
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida), contextlib.redirect_stderr(saida):
            codigo = self.modulo.main(["--raiz", os.path.join(self.raiz, "nao-existe"), "--hoje", HOJE])
        # reprova se: `if not os.path.isdir(raiz): raise InstrumentoQuebrado` sumir de calcula()
        self.assertEqual(codigo, 2)
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                self.modulo.main(["--dias", "0"])
            with self.assertRaises(SystemExit):
                self.modulo.main(["--dry-run", "--gravar"])


if __name__ == "__main__":
    unittest.main()
