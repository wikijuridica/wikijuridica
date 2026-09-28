#!/usr/bin/env python3
"""Testes de tools/generate-painel — só fixtures pequenas numa raiz temporária,
nunca os ledgers reais (o run-qualidade-diaria envelopa cada teste em timeout).

O que estes testes travam:
  - "última linha por dia vence" nos ledgers append-only (edge_traffic, Bing);
  - ausência de TODA série não quebra: o HTML nasce com todas as seções de
    SECOES e os 7 JSON saem com `schema_version: painel_v1`, marcando
    "sem série ainda";
  - a seção Previsão só LÊ data/ops/painel/previsao.json (escrito por
    tools/generate-previsao-audiencia): o painel não o regrava, mostra por
    série o último valor, a taxa semanal com IC e as três projeções, e diz
    "ainda sem previsão" com o motivo quando o arquivo falta;
  - o HTML não carrega recurso externo: nenhum `<script`, nenhum `<link href=http`,
    nenhum `src=`/`href=` apontando para http(s);
  - o último dia é provisório e o dia anterior é o "último dia completo";
  - a travessia origem÷borda reproduz o número de cache_baseline_daily;
  - o parser de escopo de purga separa tudo / por URL / por tag;
  - a fila (sqlite, mode=ro) e as contagens sociais entram só agregadas;
  - o JSON não é regravado quando só `gerado_em` mudou (o timer de 3 h não
    pode sujar a árvore do git);
  - o HTML fica abaixo do teto de 400 KB.
"""
import importlib.util
import base64
import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FERRAMENTA = os.path.join(RAIZ, "tools", "generate-painel")
HOJE = "2026-09-09"
ONTEM = "2026-09-08"


def carrega_modulo():
    loader = SourceFileLoader("generate_painel", FERRAMENTA)
    spec = importlib.util.spec_from_loader("generate_painel", loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


def escreve_jsonl(caminho, linhas):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as handle:
        for linha in linhas:
            handle.write(json.dumps(linha, ensure_ascii=False) + "\n")


# Forma real da saída de tools/generate-previsao-audiencia (schema previsao_v1),
# com uma série projetada, uma sem série e uma área.
PREVISAO_FIXTURE = {
    "schema_version": "previsao_v1", "date": HOJE, "gerado_em": "2026-09-09T07:10:00+00:00",
    "janela_dias": 60, "janela": {"inicio": "2026-07-12", "fim": HOJE}, "ultimo_dia_completo": ONTEM,
    "modelo": "log(y+1) = a + b·t + Σ dummies(dia da semana); MQO; IC por t com df = n − posto(X)",
    "horizontes": [30, 90, 180], "minimo_dias": 21,
    "series": {
        "borda.organic_requests": {
            "n": 24, "dias_janela": 60, "dias_provisorios_excluidos": ["2026-08-13", HOJE],
            "primeiro_dia": "2026-08-12", "ultimo_dia": ONTEM, "ultimo_valor": 78835, "media_ultimos_7": 100236.7,
            "zeros": 0, "taxa_semanal_pct": 86.8, "ic80": [36.5, 155.6], "ic95": [13.6, 207.2], "r2": 0.3,
            "sigma_log": 0.7, "graus_de_liberdade": 16,
            "previsao": {
                "30": {"data": "2026-10-08", "ponto": 3686647.0, "ic80": [800000.0, 17000000.0],
                       "ic95": [400000.0, 34000000.0], "acumulado": 40000000.0},
                "90": {"data": "2026-12-07", "ponto": 396569209.0, "ic80": [1.0e7, 1.6e10],
                       "ic95": [3.0e6, 5.0e10], "acumulado": 5.0e9},
                "180": {"data": "2027-03-07", "ponto": 1115554464455.0, "ic80": [1.0e10, 1.0e14],
                        "ic95": [1.0e9, 1.0e15], "acumulado": 1.0e13}},
            "motivo": None, "detalhe": None},
        "bots.claude-user": {
            "n": 10, "dias_janela": 60, "dias_provisorios_excluidos": [HOJE], "primeiro_dia": "2026-08-26",
            "ultimo_dia": ONTEM, "ultimo_valor": 3, "media_ultimos_7": 0.9, "zeros": 7,
            "taxa_semanal_pct": None, "ic80": None, "ic95": None, "r2": None, "sigma_log": None,
            "graus_de_liberdade": None, "previsao": None, "motivo": "sem_serie_suficiente",
            "detalhe": "10 dia(s) com dado na janela 2026-07-12 → 2026-09-09 (provisórios excluídos: 1); mínimo 21"}},
    "areas": [{"area": "glossario", "paginas_publicadas": 942, "leituras_14d": 3421,
               "por_agente": {"amazonbot": 1375, "perplexitybot": 1125}, "leituras_por_pagina": 3.6317,
               "valor_esperado": 5203.0, "posicao": 1}],
    "areas_meta": {"janela": {"inicio": "2026-08-26", "fim": ONTEM, "dias": 14}, "fator_serie": "bots.total",
                   "fator_taxa_semanal_pct": 52.1, "fator": 1.521},
    "fontes": {"edge_traffic": "data/ops/edge_traffic_daily.jsonl"},
    "ressalvas": ["Ponto = e^ŷ − 1 (mediana condicional, não média)."],
}


def monta_fixture(raiz):
    ops = os.path.join(raiz, "data", "ops")
    escreve_jsonl(os.path.join(ops, "edge_traffic_daily.jsonl"), [
        {"date": ONTEM, "requests": 100, "self_warming_requests": 10, "organic_requests": 90,
         "page_views": 50, "uniques": 5, "schema_version": "edge_traffic_daily_v5"},
        {"date": ONTEM, "requests": 150943, "self_warming_requests": 72108, "organic_requests": 78835,
         "page_views": 80194, "uniques": 716, "schema_version": "edge_traffic_daily_v5"},
        {"date": HOJE, "requests": 80668, "self_warming_requests": 20612, "organic_requests": 60056,
         "page_views": 35795, "uniques": 716, "schema_version": "edge_traffic_daily_v5",
         "self_warming_note": "dia em curso: bruto e aquecimento ainda crescendo",
         "organic_requests_basis": "provisional_raw_minus_warming_ledger"},
    ])
    escreve_jsonl(os.path.join(ops, "edge_bot_agents_daily.jsonl"), [
        {"date": ONTEM, "agent_key": "gptbot", "function": "training", "requests_sampled": 2,
         "requests_sampled_ip_range": 0, "requests_sampled_cloudflare_verified": 2, "requests_estimated": 2,
         "schema_version": "edge_bot_agents_daily_v4"},
        {"date": ONTEM, "agent_key": "bingbot", "function": "search", "requests_sampled": 450,
         "requests_sampled_ip_range": 1, "requests_sampled_cloudflare_verified": 449, "requests_estimated": 450,
         "schema_version": "edge_bot_agents_daily_v4"},
        # PerplexityBot real: a Cloudflare nao o verifica, a faixa de IP oficial sim —
        # e o v4 exige requests_sampled = cloudflare_verified + ip_range, senao a
        # serie saneada descarta a linha.
        {"date": ONTEM, "agent_key": "perplexitybot", "function": "search", "requests_sampled": 169,
         "requests_sampled_ip_range": 169, "requests_sampled_cloudflare_verified": 0, "requests_estimated": 169,
         "authenticity": "ip_range_at_edge", "schema_version": "edge_bot_agents_daily_v4"},
        # Linha fisicamente impossivel (estimado abaixo do amostrado): a serie
        # saneada tem de descarta-la em vez de soma-la.
        {"date": ONTEM, "agent_key": "claudebot", "function": "training", "requests_sampled": 500,
         "requests_sampled_ip_range": 0, "requests_sampled_cloudflare_verified": 500, "requests_estimated": 10,
         "schema_version": "edge_bot_agents_daily_v4"},
        # Linha v1 real: tem os dois contadores (a serie saneada descarta quem nao tem)
        # e nenhuma perna de verificacao — cai em requests_sampled.
        {"date": "2026-09-07", "agent_key": "bingbot", "function": "search", "requests_estimated": 300,
         "requests_sampled": 300, "schema_version": "edge_bot_agents_daily_v1"},
        # SEO bot com o maior volume da janela: fica fora do grafico de IA e cai em `outros`.
        {"date": ONTEM, "agent_key": "semrushbot", "function": "seo", "requests_sampled": 3613,
         "requests_sampled_ip_range": 0, "requests_sampled_cloudflare_verified": 3613, "requests_estimated": 3613,
         "schema_version": "edge_bot_agents_daily_v4"},
    ])
    escreve_jsonl(os.path.join(ops, "origin_bot_traffic_daily.jsonl"), [
        {"date": ONTEM, "agent_key": "gptbot", "requests_authentic": 13000, "summable": True,
         "schema_version": "origin_bot_traffic_daily_v3"},
        {"date": ONTEM, "agent_key": "gptbot", "requests_authentic": 67, "summable": True,
         "schema_version": "origin_bot_traffic_daily_v3"},
        {"date": ONTEM, "agent_key": "gptbot", "requests_authentic": 999999, "summable": False,
         "schema_version": "origin_bot_traffic_daily_v3"},
        {"date": ONTEM, "agent_key": "bingbot", "requests_authentic": 292, "summable": True,
         "schema_version": "origin_bot_traffic_daily_v3"},
        {"date": ONTEM, "agent_key": "perplexitybot", "requests_authentic": 82, "summable": True,
         "schema_version": "origin_bot_traffic_daily_v3"},
    ])
    escreve_jsonl(os.path.join(ops, "cache_baseline_daily.jsonl"), [
        {"date": ONTEM, "schema_version": "cache_baseline_v1", "graphql_disponivel": True,
         "cache_status": {"total_requests": 150508, "por_status": {
             "hit": {"requests": 127424, "pct": 84.66}, "miss": {"requests": 18455, "pct": 12.26}}},
         "cache_status_sem_trafego_proprio": {"por_status": {"hit": {"requests": 3998, "pct": 36.51}}},
         "share_autoaquecimento": {"share": 0.4777}, "misses_do_aquecedor": {"requests": 14327},
         "misses_total": {"requests": 18455}, "purgas_tudo": 1,
         "purgas_url": {"execucoes": 2, "urls": 3}, "purgas_tag": {"execucoes": 0, "tags": 0},
         "travessia_por_bot": {
             "gptbot": {"borda": 2, "origem": 13067, "travessia": 6533.5, "status": "ok"},
             "bingbot": {"borda": 450, "origem": 292, "travessia": 0.6489, "status": "ok"},
             "perplexitybot": {"borda": 169, "origem": 82, "travessia": 0.4852, "status": "ok"},
             "semrushbot": {"borda": 3613, "origem": 0, "travessia": 0.0, "status": "ok"}}},
    ])
    escreve_jsonl(os.path.join(ops, "edge_cache_purge.jsonl"), [
        {"purged_at": ONTEM + "T10:00:00+00:00", "scope": "tudo", "success": True},
        {"purged_at": ONTEM + "T11:00:00+00:00", "scope": "25 URL(s) em 1 lote(s); 31 tag(s) em 1 lote(s)", "success": True},
        {"purged_at": ONTEM + "T12:00:00+00:00", "scope": "2 URL(s) em 1 lote(s)", "success": True},
        {"purged_at": ONTEM + "T13:00:00+00:00", "scope": "tudo", "success": False},
    ])
    escreve_jsonl(os.path.join(ops, "edge_cache_warm.jsonl"), [
        {"finished_at": ONTEM + "T01:00:00+00:00", "urls": 30, "cache_status": {"hit": 1, "miss": 29},
         "cobertura_pre_head": {"hit": 10, "miss": 30, "sem_head": 5}, "so_frios": False},
        {"finished_at": ONTEM + "T12:00:00+00:00", "urls": 10307, "cache_status": {"hit": 10201, "revalidated": 106},
         "cobertura_pre_head": {"hit": 10200, "miss": 1, "revalidated": 106, "sem_head": 0}, "so_frios": True},
    ])
    escreve_jsonl(os.path.join(ops, "radar_ia_daily.jsonl"), [
        {"date": ONTEM, "leituras_por_agente": {"gptbot": 1, "bingbot": 2}, "markdown_por_agente": {"gptbot": 0, "bingbot": 1}},
        {"date": ONTEM, "leituras_por_agente": {"gptbot": 27516, "bingbot": 136}, "markdown_por_agente": {"gptbot": 13792, "bingbot": 21}},
    ])
    escreve_jsonl(os.path.join(ops, "bot_return_daily.jsonl"), [
        {"date": ONTEM, "agent_key": "bingbot", "funcao": "search", "veio_hoje": True, "dias_desde_visita_anterior": 1,
         "requisicoes": 450, "cobertura_acumulada_pct": 99.75, "urls_novas_no_dia": 0, "citacao_clique_de_volta": 0},
    ])
    escreve_jsonl(os.path.join(ops, "bing_webmaster_daily.jsonl"), [
        {"tipo": "busca_diaria", "Date": ONTEM, "Impressions": "1", "Clicks": "0"},
        {"tipo": "busca_diaria", "Date": ONTEM, "Impressions": "42", "Clicks": "3"},
        {"tipo": "rastreio_diario", "Date": ONTEM, "InIndex": "1234", "CrawledPages": "77", "Code5xx": "0", "CrawlErrors": "0", "InLinks": "9"},
        {"tipo": "consulta_diaria", "Date": ONTEM, "Query": "wiki juridica", "Impressions": "5", "Clicks": "1", "AvgImpressionPosition": "1"},
        {"tipo": "consulta_diaria", "Date": ONTEM, "Query": "divorcio", "Impressions": "9", "Clicks": "0", "AvgImpressionPosition": "4"},
        {"tipo": "pagina_diaria", "Date": ONTEM, "Query": "https://wikijuridica.com.br/", "Impressions": "2", "Clicks": "0", "AvgImpressionPosition": "4"},
        {"tipo": "url_info", "Url": "https://wikijuridica.com.br/a/", "LastCrawledDate": "None", "HttpStatus": "0", "coletado_em": HOJE + "T14:00:00+00:00"},
        {"tipo": "url_info", "Url": "https://wikijuridica.com.br/b/", "LastCrawledDate": "2026-09-01T00:00:00", "HttpStatus": "200", "coletado_em": HOJE + "T14:00:00+00:00"},
    ])
    escreve_jsonl(os.path.join(ops, "clarity_insights_daily.jsonl"), [
        {"coletado_em": ONTEM + "T09:10:00+00:00", "janela_dias": 3, "dimensoes": ["Device"], "metricas": [
            {"metricName": "Traffic", "information": [
                {"totalSessionCount": 24, "totalBotSessionCount": 4, "distinctUserCount": 24, "Device": "Mobile"},
                {"totalSessionCount": 91, "totalBotSessionCount": 11, "distinctUserCount": 90, "Device": "PC"}]},
            {"metricName": "DeadClickCount", "information": [
                {"sessionsCount": 24, "subTotal": 4, "Device": "Mobile"}, {"sessionsCount": 91, "subTotal": 32, "Device": "PC"}]},
            {"metricName": "ScrollDepth", "information": [{"averageScrollDepth": 40.0, "Device": "Mobile"}, {"averageScrollDepth": 60.0, "Device": "PC"}]},
            {"metricName": "EngagementTime", "information": [{"totalTime": 80, "activeTime": 37, "Device": "Mobile"}]}]},
        {"coletado_em": ONTEM + "T09:20:00+00:00", "janela_dias": 1, "dimensoes": ["URL"], "metricas": [
            {"metricName": "Traffic", "information": [
                {"totalSessionCount": 0, "Url": None},
                {"totalSessionCount": 3, "totalBotSessionCount": 0, "distinctUserCount": 1, "Url": "https://wikijuridica.com.br/trabalhista/minimo-proporcional/"},
                {"totalSessionCount": 1, "totalBotSessionCount": 1, "distinctUserCount": 2, "Url": "https://wikijuridica.com.br/tributario/x/"}]},
            {"metricName": "DeadClickCount", "information": [
                {"subTotal": 2, "Url": "https://wikijuridica.com.br/trabalhista/minimo-proporcional/"}]}]},
    ])
    escreve_jsonl(os.path.join(ops, "ia_local_daily.jsonl"), [
        {"date": ONTEM, "tipo": "embed_pagina", "modelo": "qwen3-embedding:0.6b", "lote": 8, "prompt_tokens": 4000,
         "eval_tokens": 0, "parede_ms": 100000, "custo_segundos_maquina": 100.0, "resultado": "ok"},
        {"date": ONTEM, "tipo": "embed_pagina", "modelo": "qwen3-embedding:0.6b", "lote": 8, "prompt_tokens": 2000,
         "eval_tokens": 0, "parede_ms": 50000, "custo_segundos_maquina": 50.0, "resultado": "ok"},
        {"date": ONTEM, "tipo": "extrair_dispositivos", "modelo": "qwen3.5:4b", "lote": 1, "prompt_tokens": 1000,
         "eval_tokens": 500, "parede_ms": 75000, "custo_segundos_maquina": 75.0, "resultado": "ok"},
        {"date": ONTEM, "tipo": "embed_pagina", "modelo": "", "lote": 8, "prompt_tokens": 0,
         "eval_tokens": 0, "parede_ms": 10, "custo_segundos_maquina": 0.01, "resultado": "erro"},
    ])
    escreve_jsonl(os.path.join(ops, "moderacao_transparencia_diaria.jsonl"), [
        {"data": ONTEM, "estado": "sem_banco", "coletas": 0, "banco_presente": False, "piso_de_agregacao": 5},
        {"data": ONTEM, "estado": "coletada", "coletas": 1, "banco_presente": True, "piso_de_agregacao": 5},
    ])
    previsao = os.path.join(ops, "painel", "previsao.json")
    os.makedirs(os.path.dirname(previsao), exist_ok=True)
    with open(previsao, "w", encoding="utf-8") as handle:
        json.dump(PREVISAO_FIXTURE, handle, ensure_ascii=False, indent=1)
    fila = os.path.join(raiz, "data", "ai", "fila.sqlite")
    os.makedirs(os.path.dirname(fila), exist_ok=True)
    con = sqlite3.connect(fila)
    con.execute("create table tarefa (id integer primary key, tipo text not null, estado text not null, payload text)")
    con.executemany("insert into tarefa (tipo, estado, payload) values (?, ?, ?)", [
        ("embed_pagina", "concluida", "{}"), ("embed_pagina", "concluida", "{}"), ("embed_pagina", "pendente", "{}"),
        ("extrair_dispositivos", "pendente", "{}"),
    ])
    con.commit()
    con.close()
    social = os.path.join(raiz, "var", "social", "social.db")
    os.makedirs(os.path.dirname(social), exist_ok=True)
    con = sqlite3.connect(social)
    for t in ("perfis", "duvidas", "respostas", "posts_blog", "follows"):
        con.execute('create table "%s" (id integer primary key, email text, nome text)' % t)
    con.executemany("insert into perfis (email, nome) values (?, ?)", [("a@b.c", "A"), ("d@e.f", "D")])
    con.execute("insert into duvidas (email, nome) values ('x@y.z', 'segredo')")
    con.commit()
    con.close()


class GeradorNaFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.modulo = carrega_modulo()
        cls.temporario = tempfile.TemporaryDirectory(prefix="painel-fixture-")
        cls.raiz = cls.temporario.name
        monta_fixture(cls.raiz)
        cls.saida = os.path.join(cls.raiz, "var", "painel", "index.html")
        cls.json_dir = os.path.join(cls.raiz, "data", "ops", "painel")
        cls.resultado = cls.modulo.gerar(cls.raiz, cls.modulo.dt.date.fromisoformat(HOJE), 7,
                                         cls.saida, cls.json_dir, commit="teste123")
        with open(cls.saida, encoding="utf-8") as handle:
            cls.html = handle.read()

    @classmethod
    def tearDownClass(cls):
        cls.temporario.cleanup()

    def json(self, nome):
        with open(os.path.join(self.json_dir, nome + ".json"), encoding="utf-8") as handle:
            return json.load(handle)

    def test_gerou_e_ficou_abaixo_do_teto(self):
        self.assertTrue(self.resultado["ok"], self.resultado)
        self.assertLessEqual(self.resultado["html_bytes"], self.modulo.TETO_HTML_BYTES)
        self.assertEqual(len(self.resultado["json_gravados"]), 7)

    def test_ultima_linha_por_dia_vence(self):
        borda = self.json("borda")
        ontem = next(t for t in borda["trafego_por_dia"] if t["date"] == ONTEM)
        self.assertEqual(ontem["requests"], 150943)
        self.assertEqual(ontem["self_warming_requests"], 72108)
        self.assertFalse(ontem["provisorio"])
        bing = self.json("bing")
        self.assertEqual(bing["busca_por_dia"][-1], {"date": ONTEM, "impressions": 42, "clicks": 3})
        social = self.json("social")
        self.assertEqual(social["moderacao_por_dia"][-1]["estado"], "coletada")
        bots = self.json("bots")
        radar = bots["radar_ia_por_dia"][-1]
        self.assertEqual(radar["leituras_por_agente"]["gptbot"], 27516)

    def test_ultimo_dia_e_provisorio(self):
        borda = self.json("borda")
        hoje = next(t for t in borda["trafego_por_dia"] if t["date"] == HOJE)
        self.assertTrue(hoje["provisorio"])
        self.assertEqual(borda["ultimo_dia_completo"], ONTEM)
        resumo = self.json("resumo")
        self.assertEqual(resumo["ultimo_dia_completo"], ONTEM)
        self.assertEqual(resumo["borda"]["requests"], 150943)

    def test_ausencia_e_nulo_nunca_zero(self):
        borda = self.json("borda")
        vazio = next(t for t in borda["trafego_por_dia"] if t["date"] == "2026-09-05")
        self.assertFalse(vazio["presente"])
        self.assertNotIn("requests", vazio)
        bots = self.json("bots")
        dia_sem_bots = next(l for l in bots["leituras_por_dia"] if l["date"] == HOJE)
        self.assertTrue(all(v is None for v in dia_sem_bots["por_agente"].values()))

    def test_travessia_bate_com_a_linha_de_base(self):
        bots = self.json("bots")
        por_agente = {t["agente"]: t for t in bots["travessia"]}
        self.assertEqual(por_agente["gptbot"]["origem"], 13067, "linha summable:false nao pode somar")
        self.assertEqual(por_agente["gptbot"]["borda"], 2)
        self.assertEqual(por_agente["gptbot"]["travessia"], 6533.5)
        self.assertEqual((por_agente["perplexitybot"]["borda"], por_agente["perplexitybot"]["borda_campo"]),
                         (169, "requests_sampled"))
        self.assertNotIn("claudebot", por_agente, "linha impossivel descartada pela serie saneada")
        self.assertIn("1 linha(s) descartada(s)", bots["ressalvas"][0])
        for agente, t in por_agente.items():
            self.assertEqual(t["travessia"], t["baseline_travessia"], agente)
        dia_v1 = next(l for l in bots["leituras_por_dia"] if l["date"] == "2026-09-07")
        self.assertEqual(dia_v1["por_agente"]["bingbot"], 300, "linha v1 sem pernas de verificacao entra pelo count")
        self.assertEqual(self.modulo._borda_valor({"requests_estimated": 300}), (300, "requests_estimated"),
                         "fallback da dedupe local, quando edgetelemetry nao esta disponivel")
        self.assertEqual(self.modulo._borda_valor({}), (None, None))
        self.assertEqual(bots["agentes_no_grafico"], ["bingbot", "perplexitybot", "gptbot", "outros"])
        self.assertEqual(bots["agentes_em_outros"], ["semrushbot"])
        self.assertEqual(bots["funcoes_por_agente"]["semrushbot"], "seo")
        ontem = next(l for l in bots["leituras_por_dia"] if l["date"] == ONTEM)
        self.assertEqual(ontem["por_agente"]["outros"], 3613)
        self.assertEqual(por_agente["semrushbot"]["funcao"], "seo", "a tabela de travessia traz todos")

    def test_escopo_de_purga(self):
        cl = self.modulo.classifica_escopo_purga
        self.assertEqual(cl("tudo"), {"tudo": 1, "url": 0, "tag": 0, "urls_total": 0, "tags_total": 0})
        self.assertEqual(cl("25 URL(s) em 1 lote(s); 31 tag(s) em 1 lote(s)"),
                         {"tudo": 0, "url": 1, "tag": 1, "urls_total": 25, "tags_total": 31})
        self.assertEqual(cl("2 URL(s) em 1 lote(s)"), {"tudo": 0, "url": 1, "tag": 0, "urls_total": 2, "tags_total": 0})
        borda = self.json("borda")
        purgas = borda["purgas_por_dia"][0]
        self.assertEqual((purgas["tudo"], purgas["url"], purgas["tag"], purgas["urls_total"], purgas["tags_total"], purgas["falhas"]),
                         (1, 2, 1, 27, 31, 1))
        aq = borda["aquecimento_por_dia"][0]
        self.assertEqual(aq["execucoes"], 2)
        self.assertAlmostEqual(aq["pre_head_hit_pct"], round(100.0 * 10200 / 10307, 2))

    def test_cerebro_fila_e_taxas(self):
        cerebro = self.json("cerebro")
        self.assertTrue(cerebro["fila"]["disponivel"])
        self.assertIn({"tipo": "embed_pagina", "estado": "concluida", "n": 2}, cerebro["fila"]["por_tipo_estado"])
        dia = cerebro["por_dia"][0]
        self.assertEqual((dia["itens"], dia["lotes"], dia["erros"]), (25, 4, 1))
        taxas = {(t["tipo"], t["modelo"]): t for t in cerebro["taxa_por_modelo"]}
        self.assertNotIn(("embed_pagina", ""), taxas, "lote com erro e sem modelo fica fora das taxas")
        emb = taxas[("embed_pagina", "qwen3-embedding:0.6b")]
        self.assertEqual(emb["prompt_tok_s"], 40.0)
        self.assertIsNone(emb["eval_tok_s"])
        ext = taxas[("extrair_dispositivos", "qwen3.5:4b")]
        self.assertEqual(ext["tok_s_total"], 20.0)

    def test_social_so_contagens(self):
        social = self.json("social")
        self.assertEqual(social["banco"]["contagens"], {"perfis": 2, "duvidas": 1, "respostas": 0, "posts_blog": 0, "follows": 0})
        texto = json.dumps(social) + self.html
        self.assertNotIn("a@b.c", texto)
        self.assertNotIn("segredo", texto)

    def test_humanos_janela_e_top_urls(self):
        humanos = self.json("humanos")
        j = humanos["janelas"][-1]
        self.assertEqual((j["sessoes"], j["sessoes_bot"], j["dead_clicks"], j["janela_dias"]), (115, 15, 36, 3))
        self.assertEqual(humanos["top_urls"]["itens"][0]["url"], "https://wikijuridica.com.br/trabalhista/minimo-proporcional/")
        self.assertEqual(humanos["top_urls"]["itens"][0]["dead_clicks"], 2)

    def test_bing_top_e_url_info(self):
        bing = self.json("bing")
        self.assertEqual(bing["top_consultas"]["itens"][0]["query"], "divorcio")
        self.assertEqual(bing["rastreio_por_dia"][-1]["in_index"], 1234)
        self.assertEqual(bing["url_info"]["com_last_crawled_date"], 1)
        self.assertIsNone(bing["envios_por_dia"])

    def test_html_nao_tem_estilo_inline_e_a_csp_do_nginx_leva_o_hash_da_folha(self):
        """O painel é servido em /painel/ sob CSP por hash (ops/nginx): a única folha
        é o <style> da constante CSS, e nenhum elemento pode carregar style="…"
        (a CSP não admite estilo inline nem 'unsafe-hashes'). Cor de série vai em
        atributo de apresentação SVG (fill/stroke), que a CSP não governa.
        O hash gravado nos dois confs do nginx tem de ser o da constante do
        gerador — mudou o CSS, muda o conf junto, ou o painel abre sem estilo."""
        self.assertNotIn('style="', self.html, "elemento com style inline no painel")
        self.assertEqual(self.html.count("<style>"), 1, "o painel tem exatamente um <style>")
        esperado = "sha256-" + base64.b64encode(
            hashlib.sha256(self.modulo.CSS.encode("utf-8")).digest()).decode("ascii")
        raiz_do_repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for conf in ("ops/nginx/wikijuridica.conf", "ops/nginx/standalone/nginx.conf"):
            with open(os.path.join(raiz_do_repo, conf), encoding="utf-8") as handle:
                texto = handle.read()
            inicio = texto.find("location ^~ /painel/")
            self.assertGreaterEqual(inicio, 0, "%s não tem a location /painel/" % conf)
            bloco = texto[inicio:texto.find("\n    }", inicio)]
            self.assertIn("style-src '%s'" % esperado, bloco,
                          "%s: o hash da CSP do painel não é o da constante CSS do gerador (%s)" % (conf, esperado))
            self.assertIn('if ($http_cf_connecting_ip != "") { return 404; }', bloco,
                          "%s: o painel tem de ser 404 para quem vem pelo túnel" % conf)

    def test_previsao_le_o_json_da_ferramenta_e_nunca_o_regrava(self):
        """A seção Previsão renderiza o previsao.json que a fixture gravou — texto e
        tabela por série, mais o ranking de áreas — e o painel NÃO regrava esse
        arquivo (é da ferramenta generate-previsao-audiencia)."""
        self.assertIn('<section class="secao" id="previsao">', self.html)
        self.assertNotIn("ainda sem previsão", self.html)
        self.assertIn("borda.organic_requests", self.html)
        self.assertIn("86,8 %", self.html, "taxa semanal da série projetada")
        self.assertIn("36,5 a 155,6", self.html, "IC80 da taxa")
        self.assertIn("2026-10-08", self.html, "data-alvo dos 30 dias")
        self.assertIn("3,69 mi", self.html, "projeção de 30 dias compactada")
        self.assertIn("1.12e+12", self.html, "projeção acima de 1e9 em notação científica")
        self.assertIn("sem_serie_suficiente", self.html)
        self.assertIn("mínimo 21", self.html, "o motivo vem com o detalhe")
        self.assertIn("glossario", self.html)
        self.assertIn("bots.total", self.html, "a legenda do ranking diz de onde vem o fator")
        self.assertIn("mediana condicional", self.html, "as ressalvas do gerador aparecem")
        resumo = self.json("resumo")
        self.assertEqual((resumo["previsao"]["disponivel"], resumo["previsao"]["series_projetadas"],
                          resumo["previsao"]["series_total"], resumo["previsao"]["top_areas"]),
                         (True, 1, 2, ["glossario"]))
        self.assertIn("data/ops/painel/previsao.json", [f["arquivo"] for f in resumo["fontes"]])
        caminho = os.path.join(self.json_dir, "previsao.json")
        self.assertNotIn(caminho, self.resultado["json_gravados"])
        with open(caminho, encoding="utf-8") as handle:
            self.assertEqual(json.load(handle), PREVISAO_FIXTURE, "o painel só lê previsao.json")
        self.assertEqual(len(self.resultado["json_gravados"]), 7, "a seção não gera um 8.º JSON")

    def test_html_tem_todas_as_secoes_e_nenhum_recurso_externo(self):
        for ident, _titulo in self.modulo.SECOES:
            self.assertIn('<section class="secao" id="%s">' % ident, self.html)
        self.assertNotIn("<script", self.html)
        self.assertNotIn("<link href=http", self.html)
        self.assertNotIn("<link", self.html)
        self.assertIsNone(re.search(r'(src|href)=["\']https?://', self.html))
        self.assertIn("gerado_em", self.html)
        self.assertIn("commit teste123", self.html)
        self.assertIn("edge_traffic_daily.jsonl", self.html)
        self.assertIn("sem série ainda", self.html)

    def test_schema_version_em_todos_os_json(self):
        for nome in ("borda", "bots", "bing", "humanos", "cerebro", "social", "resumo"):
            dados = self.json(nome)
            self.assertEqual(dados["schema_version"], "painel_v1", nome)
            self.assertEqual(dados["commit"], "teste123", nome)
        resumo = self.json("resumo")
        self.assertEqual(list(resumo)[:5], ["schema_version", "gerado_em", "commit", "hoje", "dias"])
        self.assertEqual(resumo["frescor"]["estado"], "sem série ainda")
        self.assertEqual(resumo["experimentos"]["estado"], "sem série ainda")

    def test_json_nao_regrava_quando_so_gerado_em_muda(self):
        caminho = os.path.join(self.json_dir, "borda.json")
        antes = os.stat(caminho).st_mtime_ns
        with open(caminho, encoding="utf-8") as handle:
            conteudo = handle.read()
        # HEAD avança varias vezes por hora: commit diferente com o mesmo conteudo
        # NAO pode regravar, senao o timer suja a arvore a cada 3 h.
        segundo = self.modulo.gerar(self.raiz, self.modulo.dt.date.fromisoformat(HOJE), 7,
                                    self.saida, self.json_dir, commit="outro456")
        self.assertTrue(segundo["ok"])
        self.assertEqual(segundo["json_gravados"], [])
        with open(self.saida, encoding="utf-8") as handle:
            self.assertIn("commit outro456", handle.read(), "o HTML leva sempre o HEAD corrente")
        self.assertEqual(os.stat(caminho).st_mtime_ns, antes)
        with open(caminho, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), conteudo)


class AusenciaDeSeries(unittest.TestCase):
    def test_raiz_vazia_gera_todas_as_secoes(self):
        modulo = carrega_modulo()
        with tempfile.TemporaryDirectory(prefix="painel-vazio-") as raiz:
            saida = os.path.join(raiz, "var", "painel", "index.html")
            json_dir = os.path.join(raiz, "data", "ops", "painel")
            resultado = modulo.gerar(raiz, modulo.dt.date.fromisoformat(HOJE), 30, saida, json_dir, commit="vazio")
            self.assertTrue(resultado["ok"], resultado)
            with open(saida, encoding="utf-8") as handle:
                html = handle.read()
            for ident, _titulo in modulo.SECOES:
                self.assertIn('id="%s"' % ident, html)
            self.assertNotIn("<script", html)
            self.assertIn("sem série ainda", html)
            self.assertIn("ainda sem previsão", html)
            self.assertIn("generate-previsao-audiencia", html, "o motivo diz quem gera o arquivo")
            with open(os.path.join(json_dir, "resumo.json"), encoding="utf-8") as handle:
                resumo = json.load(handle)
            self.assertEqual(resumo["schema_version"], "painel_v1")
            self.assertFalse(resumo["previsao"]["disponivel"])
            self.assertIn("arquivo ausente", resumo["previsao"]["motivo"])
            self.assertIsNone(resumo["borda"]["requests"])
            self.assertFalse(resumo["cerebro"]["fila_disponivel"])
            self.assertFalse(resumo["social"]["banco_disponivel"])
            self.assertTrue(all(not f["existe"] for f in resumo["fontes"]))
            with open(os.path.join(json_dir, "bots.json"), encoding="utf-8") as handle:
                bots = json.load(handle)
            self.assertEqual(bots["travessia"], [])
            self.assertEqual(len(bots["leituras_por_dia"]), 30)

    def test_cli_recusa_dias_invalido(self):
        modulo = carrega_modulo()
        with self.assertRaises(SystemExit):
            modulo.main(["--dias", "0"])


class BingSubmitPorDia(unittest.TestCase):
    """O painel tem de CONTAR as submissões que o ledger realmente gravou.

    Medido em 2026-09-10: o ledger `data/ops/bing_submit_ledger.jsonl` tinha 200
    linhas com a chave `submetido_em`, e o painel procurava por `date`,
    `submitted_at` e `ts` — três chaves inglesas que nunca existiram ali. O
    resultado era pior que um erro: `submit.existe` era true, a seção aparecia
    com `envios_por_dia: []` e nenhuma ressalva acusava. Duzentas submissões
    reais ao Bing, invisíveis para quem lê o painel.
    """

    def test_conta_pela_chave_do_ledger_real(self):
        fonte = open(os.path.join(RAIZ, "tools", "generate-painel"), encoding="utf-8").read()
        linha = [l for l in fonte.splitlines() if 'r.get("submetido_em")' in l]
        self.assertTrue(linha, "o painel voltou a ignorar a chave real do ledger do Bing")
        # A chave real vem ANTES das inglesas: se `date` vier primeiro e um dia
        # existir por acaso, a contagem volta a mentir sem ninguém ver.
        posicao = linha[0].index('r.get("submetido_em")')
        for chave in ('r.get("date")', 'r.get("submitted_at")', 'r.get("ts")'):
            if chave in linha[0]:
                self.assertLess(posicao, linha[0].index(chave),
                                "a chave real do ledger tem de ter precedência sobre as inglesas")

if __name__ == "__main__":
    unittest.main()
