#!/usr/bin/env python3
"""Testes de tools/generate-cache-baseline — sem rede: a consulta GraphQL e a
resolução da zona são injetadas.

O que estes testes travam:
  - a agregação do dia (cache_status, misses do aquecedor, misses por família
    de bot com casamento por substring em minúsculas, fatias que FECHAM com o
    total de MISS);
  - travessia com denominador zero: nunca divide por zero, marca
    `nao_mensuravel`; e a borda usa `requests_sampled` (o count, total
    verificado no v4), com a faixa de IP só como fallback e o
    `requests_estimated` do produtor gravado ao lado;
  - `misses_pre_head_sem_purga`, com PROVA POR MUTAÇÃO: o teste reescreve o
    guarda de exclusão da hora pós-purga por `if False:` no próprio código
    fonte, executa o mutante e exige que o número MUDE. Se um dia a exclusão
    virar código morto, este teste fica vermelho;
  - purga falha (`success: false`) não exclui varredura;
  - linha idêntica (ignorando `gerado_em`) não se regrava;
  - sem credencial: exit 2, mas a linha do disco sai gravada com
    `graphql_disponivel: false`;
  - a JANELA dos casos de ponta a ponta se CALCULA do relógio, dentro de
    RETENCAO_DIAS lida do próprio produtor, e a fixture real de 2026-09-08 é
    realocada para ela — ver o bloco "as DUAS datas desta bancada" abaixo.
"""
import datetime as dt
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FERRAMENTA = os.path.join(RAIZ, "tools", "generate-cache-baseline")


def carrega_modulo(nome="generate_cache_baseline", fonte=None):
    """Carrega a ferramenta (sem extensão .py). Com `fonte`, executa ESSE
    texto no lugar do arquivo — é assim que o mutante nasce."""
    loader = SourceFileLoader(nome, FERRAMENTA)
    spec = importlib.util.spec_from_loader(nome, loader)
    modulo = importlib.util.module_from_spec(spec)
    if fonte is None:
        loader.exec_module(modulo)
    else:
        modulo.__file__ = FERRAMENTA
        exec(compile(fonte, FERRAMENTA, "exec"), modulo.__dict__)
    return modulo


# ─────────────────────── as DUAS datas desta bancada ─────────────────────────
#
# DIA_CONGELADO é o dia real de 2026-09-08, congelado aqui como fixture própria:
# as varreduras, as purgas e os grupos do GraphQL abaixo são o que a borda
# devolveu naquele dia. Ele alimenta SÓ as funções puras (agregação, partição de
# MISS, travessia, share, purgas do dia), que não consultam relógio nenhum e
# portanto não envelhecem — congelar dado velho é o certo, e lê-lo do disco vivo
# seria o errado.
#
# DIA é outra coisa: é o dia que `main()` vai consultar, e `main()` COMPARA com o
# relógio (`hoje - dia > RETENCAO_DIAS` ⇒ `fora_da_retencao`). Uma data absoluta
# aqui é uma bomba-relógio — foi exatamente assim que esta bancada ficou vermelha
# em 2026-09-16: o 2026-09-08 escrito à mão saiu da retenção de 8 dias e o
# `--dias 2` passou a pedir um 2026-09-07 que a Cloudflare já não tem. Por isso a
# janela se CALCULA a partir do relógio, no mesmo default da ferramenta (ontem),
# e `test_a_janela_da_bancada_cabe_na_retencao` declara a borda: se
# RETENCAO_DIAS encolher, o vermelho diz qual é a causa em vez de "2 != 0".
DIA_CONGELADO = dt.date(2026, 9, 8)
HOJE = dt.datetime.now(dt.timezone.utc).date()
DIA = HOJE - dt.timedelta(days=1)


def realoca(valor, de=DIA_CONGELADO, para=DIA):
    """Recoloca a fixture congelada na janela de retenção vigente.

    Troca a data de `de` por `para` (e a véspera de `de` pela véspera de `para`)
    dentro de qualquer string, preservando hora, minuto, segundo e fuso — o que
    se move é o dia, não o formato nem o conteúdo medido. Recursivo em dict e
    list. As duas substituições são feitas em UM passe por chave, nunca em
    cascata: substituir sequencialmente permitiria que a saída da primeira
    virasse entrada da segunda."""
    mapa = {de.isoformat(): para.isoformat(),
            (de - dt.timedelta(days=1)).isoformat(): (para - dt.timedelta(days=1)).isoformat()}
    if isinstance(valor, dict):
        return {k: realoca(v, de, para) for k, v in valor.items()}
    if isinstance(valor, list):
        return [realoca(v, de, para) for v in valor]
    if isinstance(valor, str):
        for origem, destino in mapa.items():
            if valor.startswith(origem):
                return destino + valor[len(origem):]
    return valor


def grupo(count, intervalo=1.0, **dims):
    return {"count": count, "avg": {"sampleInterval": intervalo},
            "sum": {"edgeResponseBytes": count * 100}, "dimensions": dims}


def resposta(grupos):
    return {"viewer": {"zones": [{"httpRequestsAdaptiveGroups": grupos}]}}


def resposta_1d(requests, bytes_, cached, dia=None):
    """`dia` é o dia PEDIDO pela consulta. O fake responde ao que foi perguntado
    em vez de a uma constante — do contrário a dimensão `date` mentiria assim que
    a bancada rodasse para um dia diferente do congelado."""
    return {"viewer": {"zones": [{"httpRequests1dGroups": [
        {"dimensions": {"date": dia or DIA_CONGELADO.isoformat()},
         "sum": {"requests": requests, "bytes": bytes_, "cachedRequests": cached, "cachedBytes": 0}}]}]}}


GRUPOS_CACHE_STATUS = [
    grupo(4020, 1.0, cacheStatus="hit"),
    grupo(4032, 1.5, cacheStatus="miss"),
    grupo(1622, 1.0, cacheStatus="dynamic"),
]


def graphql_falso(consulta, variaveis, **kw):
    """Responde às quatro consultas da ferramenta com as fixtures acima."""
    if "httpRequests1dGroups" in consulta:
        return resposta_1d(9700, 967400, 4040, variaveis.get("dia")), ""
    if 'cacheStatus: "miss"' in consulta:
        return resposta(GRUPOS_MISSES), ""
    return resposta(GRUPOS_CACHE_STATUS), ""

GRUPOS_MISSES = [
    grupo(1000, 3.0, userAgent="wikijuridica-cache-warm/1.0 (+interno)", verifiedBotCategory=""),
    grupo(40, 1.0, userAgent="wikijuridica-superficie-probe/1.0", verifiedBotCategory=""),
    grupo(268, 1.0, userAgent="Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
          verifiedBotCategory="Search Engine Crawler"),
    grupo(72, 1.0, userAgent="Mozilla/5.0 (compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)",
          verifiedBotCategory=""),
    grupo(150, 1.0, userAgent="Mozilla/5.0; compatible; ChatGPT-User/1.0; +https://openai.com/bot",
          verifiedBotCategory="AI Assistant"),
    grupo(9, 1.0, userAgent="Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
          verifiedBotCategory="Search Engine Crawler"),
    grupo(2415, 1.0, userAgent="Mozilla/5.0 (compatible; SemrushBot/7~bl)", verifiedBotCategory=""),
    grupo(407, 1.0, userAgent="Mozilla/5.0 (Macintosh) Chrome/126", verifiedBotCategory=""),
]


class TestAgregacaoDoDia(unittest.TestCase):
    def setUp(self):
        self.mod = carrega_modulo()

    def test_cache_status_conta_percentua_e_nao_extrapola(self):
        r = self.mod.agrega_cache_status(GRUPOS_CACHE_STATUS)
        self.assertEqual(r["total_requests"], 4020 + 4032 + 1622)
        self.assertEqual(r["por_status"]["miss"]["requests"], 4032)
        # count × sampleInterval NAO entra como numero: so o intervalo medio, informativo
        self.assertNotIn("estimated", r["por_status"]["miss"])
        self.assertEqual(r["por_status"]["miss"]["sample_interval_medio"], 1.5)
        self.assertAlmostEqual(r["por_status"]["hit"]["pct"], 100 * 4020 / 9674, places=2)
        self.assertEqual(r["por_status"]["hit"]["bytes"], 402000)
        self.assertEqual(r["total_bytes"], 967400)

    def test_cache_status_vazio_nao_divide_por_zero(self):
        r = self.mod.agrega_cache_status([])
        self.assertEqual(r["total_requests"], 0)
        self.assertEqual(r["por_status"], {})

    def test_conferencia_exata_confronta_count_com_o_1d(self):
        cs = self.mod.agrega_cache_status(GRUPOS_CACHE_STATUS)
        grupos_1d = self.mod.grupos_1d_de(resposta_1d(9700, 967400, 4040))
        c = self.mod.conferencia_exata(cs, grupos_1d)
        self.assertEqual(c["requests_1d"], 9700)
        self.assertEqual(c["cached_requests_1d"], 4040)
        self.assertAlmostEqual(c["razao_requests"], 9674 / 9700, places=4)
        self.assertAlmostEqual(c["razao_hit"], 4020 / 4040, places=4)
        vazio = self.mod.conferencia_exata(cs, [])
        self.assertIsNone(vazio["requests_1d"])
        self.assertIsNone(vazio["razao_requests"])

    def test_misses_reparte_em_fatias_disjuntas_que_fecham(self):
        r = self.mod.particiona_misses(GRUPOS_MISSES)
        self.assertEqual(r["misses_do_aquecedor"], {
            "requests": 1000, "sample_interval_medio": 3.0,
            "user_agents": ["wikijuridica-cache-warm/1.0 (+interno)"]})
        self.assertEqual(r["misses_trafego_proprio_outros"]["requests"], 40)
        bots = r["misses_de_bots_verificados"]
        # casamento por substring em minúsculas: "PerplexityBot", "ChatGPT-User", "Googlebot"
        self.assertEqual(bots["perplexitybot"], {"requests": 72, "cloudflare_verified": 0})
        self.assertEqual(bots["chatgpt-user"]["requests"], 150)
        self.assertEqual(bots["chatgpt-user"]["cloudflare_verified"], 150)
        self.assertEqual(bots["bingbot"]["requests"], 268)
        self.assertEqual(bots["googlebot"]["requests"], 9)
        self.assertEqual(bots["gptbot"]["requests"], 0, "ChatGPT-User nao contem 'gptbot'")
        self.assertEqual(r["misses_restantes"]["requests"], 2415 + 407)
        soma = (r["misses_do_aquecedor"]["requests"] + r["misses_trafego_proprio_outros"]["requests"]
                + sum(v["requests"] for v in bots.values()) + r["misses_restantes"]["requests"])
        self.assertEqual(soma, r["misses_total"]["requests"])
        self.assertEqual(r["misses_total"]["requests"], sum(g["count"] for g in GRUPOS_MISSES))
        self.assertFalse(r["query_truncated"])

    def test_teto_batido_marca_truncamento(self):
        grupos = [grupo(1, 1.0, userAgent="ua%d" % i, verifiedBotCategory="") for i in range(5)]
        self.assertTrue(self.mod.particiona_misses(grupos, limite=5)["query_truncated"])

    def test_consultar_dia_monta_bloco_com_as_quatro_consultas(self):
        chamadas = []

        def falso_graphql(consulta, variaveis, **kw):
            chamadas.append((consulta, variaveis))
            return graphql_falso(consulta, variaveis)

        self.mod.GRAPHQL = falso_graphql
        bloco, erro = self.mod.consultar_dia("zona-x", DIA_CONGELADO)
        self.assertIsNone(erro)
        self.assertEqual(len(chamadas), 4)
        self.assertEqual(chamadas[0][1]["since"], "2026-09-08T00:00:00Z")
        self.assertEqual(chamadas[0][1]["until"], "2026-09-08T23:59:59Z")
        self.assertIn("httpRequests1dGroups", chamadas[1][0])
        self.assertEqual(chamadas[1][1]["dia"], "2026-09-08")
        self.assertIn("userAgent_notlike", chamadas[2][0])
        self.assertNotIn("userAgent_notlike", chamadas[3][0], "a consulta de MISS precisa ver o aquecedor")
        self.assertEqual(bloco["misses_do_aquecedor"]["requests"], 1000)
        self.assertEqual(bloco["cache_status"]["por_status"]["hit"]["requests"], 4020)
        self.assertAlmostEqual(bloco["conferencia_exata"]["razao_requests"], 9674 / 9700, places=4)

    def test_erro_em_qualquer_consulta_devolve_bloco_nenhum(self):
        self.mod.GRAPHQL = lambda consulta, variaveis, **kw: (None, "cannot request a time range wider than 1d")
        bloco, erro = self.mod.consultar_dia("zona-x", DIA_CONGELADO)
        self.assertIsNone(bloco)
        self.assertIn("wider than 1d", erro)


class TestTravessia(unittest.TestCase):
    def setUp(self):
        self.mod = carrega_modulo()

    def borda(self, agente, sampled, faixa_ip=0, cf=None, estimado=None):
        return {(DIA_CONGELADO.isoformat(), agente): {
            "agent_key": agente, "date": DIA_CONGELADO.isoformat(),
            "requests_sampled": sampled, "requests_sampled_ip_range": faixa_ip,
            "requests_sampled_cloudflare_verified": cf if cf is not None else sampled - faixa_ip,
            "requests_estimated": estimado if estimado is not None else sampled}}

    def origem(self, agente, *deltas, campo="requests_authentic", summable=True):
        return [{"date": DIA_CONGELADO.isoformat(), "agent_key": agente, campo: d, "summable": summable}
                for d in deltas]

    def test_denominador_zero_marca_nao_mensuravel_sem_excecao(self):
        borda = self.borda("claudebot", 0)
        r = self.mod.travessia_por_bot(DIA_CONGELADO, borda, self.origem("claudebot", 4))
        self.assertEqual(r["claudebot"]["status"], "nao_mensuravel")
        self.assertIsNone(r["claudebot"]["travessia"])
        self.assertEqual(r["claudebot"]["origem"], 4)
        self.assertEqual(r["claudebot"]["borda"], 0)

    def test_bot_so_na_origem_tambem_e_nao_mensuravel(self):
        r = self.mod.travessia_por_bot(DIA_CONGELADO, {}, self.origem("gptbot", 13067))
        self.assertEqual(r["gptbot"]["status"], "nao_mensuravel")
        self.assertEqual(r["gptbot"]["origem"], 13067)

    def test_origem_soma_deltas_e_borda_usa_total_verificado(self):
        # bingbot 2026-09-08: requests_sampled 450 (total verificado), faixa de IP 1.
        borda = self.borda("bingbot", 450, faixa_ip=1, estimado=463)
        r = self.mod.travessia_por_bot(DIA_CONGELADO, borda, self.origem("bingbot", 100, 150, 42))
        self.assertEqual(r["bingbot"]["origem"], 292)
        self.assertEqual(r["bingbot"]["origem_linhas"], 3)
        self.assertEqual(r["bingbot"]["borda"], 450)
        self.assertEqual(r["bingbot"]["borda_campo"], "requests_sampled")
        self.assertEqual(r["bingbot"]["borda_ip_range"], 1)
        self.assertEqual(r["bingbot"]["borda_estimated_produtor"], 463)
        self.assertAlmostEqual(r["bingbot"]["travessia"], 292 / 450, places=4)
        self.assertEqual(r["bingbot"]["status"], "ok")
        self.assertFalse(r["bingbot"]["origem_acima_da_borda"])

    def test_faixa_de_ip_so_como_fallback_quando_total_zerado(self):
        borda = self.borda("perplexitybot", 0, faixa_ip=169)
        r = self.mod.travessia_por_bot(DIA_CONGELADO, borda, self.origem("perplexitybot", 82))
        self.assertEqual(r["perplexitybot"]["borda"], 169)
        self.assertEqual(r["perplexitybot"]["borda_campo"], "requests_sampled_ip_range")

    def test_origem_acima_da_borda_e_marcada_nao_escondida(self):
        borda = self.borda("gptbot", 2)
        r = self.mod.travessia_por_bot(DIA_CONGELADO, borda, self.origem("gptbot", 13067))
        self.assertTrue(r["gptbot"]["origem_acima_da_borda"])
        self.assertAlmostEqual(r["gptbot"]["travessia"], 6533.5, places=1)

    def test_linha_v2_sem_requests_authentic_usa_requests(self):
        r = self.mod.travessia_por_bot(DIA_CONGELADO, self.borda("yandexbot", 17),
                                       self.origem("yandexbot", 14, campo="requests"))
        self.assertEqual(r["yandexbot"]["origem"], 14)
        self.assertEqual(r["yandexbot"]["origem_campo"], "requests")

    def test_linha_nao_somavel_fica_de_fora(self):
        r = self.mod.travessia_por_bot(DIA_CONGELADO, self.borda("bingbot", 10),
                                       self.origem("bingbot", 5, summable=False) + self.origem("bingbot", 3))
        self.assertEqual(r["bingbot"]["origem"], 3)

    def test_outro_dia_nao_entra(self):
        borda = {("2026-09-07", "bingbot"): {"requests_sampled": 999}}
        origem = [{"date": "2026-09-07", "agent_key": "bingbot", "requests_authentic": 5, "summable": True}]
        self.assertEqual(self.mod.travessia_por_bot(DIA_CONGELADO, borda, origem), {})


def varredura(inicio, fim, miss, so_frios=True):
    return {"started_at": inicio, "finished_at": fim, "so_frios": so_frios,
            "cobertura_pre_head": {"hit": 10000, "miss": miss}, "urls": 10302}


def purga(quando, escopo="6 URL(s) em 1 lote(s)", sucesso=True):
    return {"purged_at": quando, "scope": escopo, "success": sucesso}


# O dia real de 2026-09-08, reduzido ao que importa (ver o cabeçalho da ferramenta).
VARREDURAS_0908 = [
    varredura("2026-09-08T00:23:28+00:00", "2026-09-08T00:37:47+00:00", 0),
    varredura("2026-09-08T04:23:20+00:00", "2026-09-08T04:37:38+00:00", 46),
    varredura("2026-09-08T08:20:32+00:00", "2026-09-08T08:34:51+00:00", 962),   # purga às 07:51/07:52
    varredura("2026-09-08T12:22:12+00:00", "2026-09-08T12:36:31+00:00", 4),
    varredura("2026-09-08T16:23:23+00:00", "2026-09-08T16:37:41+00:00", 0),
    varredura("2026-09-08T20:24:12+00:00", "2026-09-08T20:38:31+00:00", 5),     # purga às 19:34
    varredura("2026-09-08T20:57:34+00:00", "2026-09-08T21:11:53+00:00", 0, so_frios=False),
    varredura("2026-09-07T20:24:12+00:00", "2026-09-07T20:38:31+00:00", 500),   # outro dia
]
PURGAS_0908 = [
    purga("2026-09-08T07:51:20+00:00"),
    purga("2026-09-08T07:52:34+00:00", "144 URL(s) em 2 lote(s); 3 tag(s) em 1 lote(s)"),
    purga("2026-09-08T19:34:30+00:00", "2 URL(s) em 1 lote(s)"),
    purga("2026-09-08T20:57:34+00:00", "tudo"),
]


class TestMissesPreHeadSemPurga(unittest.TestCase):
    def setUp(self):
        self.mod = carrega_modulo()

    def test_exclui_varredura_na_hora_pos_purga(self):
        r = self.mod.misses_pre_head_sem_purga(DIA_CONGELADO, VARREDURAS_0908, PURGAS_0908)
        self.assertEqual(r["total"], 0 + 46 + 4 + 0)
        self.assertEqual(r["varreduras_so_frios"], 6)
        self.assertEqual(r["varreduras_contadas"], 4)
        self.assertEqual(r["varreduras_excluidas_por_purga"], 2)
        self.assertEqual(r["janela_s"], 3600)

    def test_purga_falha_nao_exclui(self):
        purgas = [purga("2026-09-08T07:52:34+00:00", sucesso=False)]
        r = self.mod.misses_pre_head_sem_purga(DIA_CONGELADO, VARREDURAS_0908, purgas)
        self.assertEqual(r["total"], 0 + 46 + 962 + 4 + 0 + 5)
        self.assertEqual(r["varreduras_excluidas_por_purga"], 0)

    def test_purga_durante_a_varredura_e_contada_como_ressalva(self):
        purgas = [purga("2026-09-08T08:30:00+00:00")]
        r = self.mod.misses_pre_head_sem_purga(DIA_CONGELADO, VARREDURAS_0908, purgas)
        self.assertEqual(r["purgas_durante_varredura"], 1)
        self.assertEqual(r["varreduras_excluidas_por_purga"], 0)

    def test_mutante_sem_exclusao_fica_vermelho(self):
        """PROVA POR MUTAÇÃO: troca o guarda de exclusão por `if False:` no
        código fonte e exige que o total MUDE. Se a exclusão for código morto,
        original e mutante coincidem e este teste reprova."""
        with open(FERRAMENTA, encoding="utf-8") as fh:
            fonte = fh.read()
        guarda = "if purga_na_janela(inicio, purgas_ok, janela_s):  # exclusao-pos-purga"
        self.assertEqual(fonte.count(guarda), 1, "o guarda mutavel precisa existir uma unica vez")
        mutante = carrega_modulo("generate_cache_baseline_mutante",
                                 fonte.replace(guarda, "if False:  # MUTANTE: exclusao desligada"))
        original = self.mod.misses_pre_head_sem_purga(DIA_CONGELADO, VARREDURAS_0908, PURGAS_0908)["total"]
        mutado = mutante.misses_pre_head_sem_purga(DIA_CONGELADO, VARREDURAS_0908, PURGAS_0908)["total"]
        print(f"\n  mutante vermelho: original={original} mutante(sem exclusao)={mutado}")
        self.assertEqual(original, 50)
        self.assertEqual(mutado, 1017)
        self.assertNotEqual(original, mutado)


class TestPurgasEShare(unittest.TestCase):
    def setUp(self):
        self.mod = carrega_modulo()

    def test_purgas_do_dia_contam_e_somam(self):
        purgas = PURGAS_0908 + [purga("2026-09-08T10:00:00+00:00", "10 tag(s) em 1 lote(s)"),
                                purga("2026-09-08T11:00:00+00:00", "1 URL(s) em 1 lote(s)", sucesso=False),
                                purga("2026-09-07T11:00:00+00:00", "tudo")]
        r = self.mod.purgas_do_dia(DIA_CONGELADO, purgas)
        self.assertEqual(r["purgas_tudo"], 1)
        self.assertEqual(r["purgas_url"], {"execucoes": 3, "urls": 6 + 144 + 2})
        self.assertEqual(r["purgas_tag"], {"execucoes": 2, "tags": 3 + 10})
        self.assertEqual(r["purgas_falhas"], 1)

    def test_share_autoaquecimento_usa_a_ultima_linha_do_dia(self):
        trafego = [{"date": "2026-09-08", "requests": 45096, "self_warming_requests": 20598},
                   {"date": "2026-09-08", "requests": 150943, "self_warming_requests": 72108,
                    "self_warming_coverage": "ledger"}]
        r = self.mod.share_autoaquecimento(DIA_CONGELADO, trafego)
        self.assertEqual(r["requests"], 150943)
        self.assertAlmostEqual(r["share"], 72108 / 150943, places=4)
        self.assertEqual(r["status"], "ok")

    def test_share_sem_linha_ou_denominador_zero(self):
        self.assertEqual(self.mod.share_autoaquecimento(DIA_CONGELADO, [])["status"], "sem_linha_no_dia")
        r = self.mod.share_autoaquecimento(DIA_CONGELADO, [{"date": "2026-09-08", "requests": 0, "self_warming_requests": 0}])
        self.assertEqual(r["status"], "nao_mensuravel")
        self.assertIsNone(r["share"])


class TestGravacaoEMain(unittest.TestCase):
    def setUp(self):
        self.mod = carrega_modulo()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        d = self.tmp.name
        self.mod.RAIZ = d
        self.mod.SAIDA = os.path.join(d, "cache_baseline_daily.jsonl")
        self.mod.BORDA = os.path.join(d, "edge_bot_agents_daily.jsonl")
        self.mod.ORIGEM = os.path.join(d, "origin_bot_traffic_daily.jsonl")
        self.mod.PURGAS = os.path.join(d, "edge_cache_purge.jsonl")
        self.mod.AQUECIMENTO = os.path.join(d, "edge_cache_warm.jsonl")
        self.mod.TRAFEGO = os.path.join(d, "edge_traffic_daily.jsonl")
        # `cloudflare_auth` é um módulo compartilhado no processo: o que se
        # troca aqui volta ao original ao fim do teste.
        ambiente_original = self.mod.cloudflare_auth.ambiente
        self.addCleanup(setattr, self.mod.cloudflare_auth, "ambiente", ambiente_original)
        # O disco da bancada é a MESMA fixture real de 2026-09-08, realocada
        # para a janela de retenção vigente: `main()` compara o dia com o
        # relógio, então dado e dia pedido têm de andar juntos. Sem a
        # realocação, um `--dia` relativo leria um disco vazio e os números
        # cairiam a zero — o teste ficaria verde medindo nada.
        self.escreve(self.mod.PURGAS, realoca(PURGAS_0908))
        self.escreve(self.mod.AQUECIMENTO, realoca(VARREDURAS_0908))
        self.escreve(self.mod.TRAFEGO, [{"date": DIA.isoformat(), "requests": 100,
                                         "self_warming_requests": 40}])
        self.escreve(self.mod.ORIGEM, [{"date": DIA.isoformat(), "agent_key": "bingbot",
                                        "requests_authentic": 292, "summable": True}])
        self.escreve(self.mod.BORDA, [{"date": DIA.isoformat(), "agent_key": "bingbot",
                                       "requests_estimated": 463, "requests_sampled": 450}])

    def escreve(self, caminho, registros):
        with open(caminho, "w", encoding="utf-8") as fh:
            for r in registros:
                fh.write(json.dumps(r) + "\n")

    def linhas(self):
        with open(self.mod.SAIDA, encoding="utf-8") as fh:
            return [json.loads(l) for l in fh if l.strip()]

    def test_a_janela_da_bancada_cabe_na_retencao(self):
        """CONTROLE DA PRÓPRIA BANCADA, e a régua vem do produtor.

        Os testes de `main()` abaixo pedem `--dias 2`, isto é, DIA e a véspera de
        DIA. Se qualquer um dos dois cair fora de RETENCAO_DIAS, a ferramenta
        marca `fora_da_retencao` e devolve 2 — e o teste morreria com um
        "2 != 0" que não diz a causa. Lendo a constante do módulo, o dia em que
        a retenção encolher este caso reprova NOMEANDO o motivo, e continua sendo
        impossível um `--dia` escrito à mão sair da janela com o tempo."""
        mais_antigo = DIA - dt.timedelta(days=1)
        self.assertLessEqual(
            (HOJE - mais_antigo).days, self.mod.RETENCAO_DIAS,
            f"a janela da bancada ({mais_antigo}..{DIA}, hoje {HOJE}) saiu da "
            f"retenção de {self.mod.RETENCAO_DIAS} dias do produtor")
        self.assertGreaterEqual((HOJE - DIA).days, 1,
                                "o dia da bancada tem de estar no passado, como o default da ferramenta")

    def test_linha_identica_nao_se_regrava(self):
        linha = {"schema_version": "cache_baseline_v1", "date": DIA.isoformat(), "x": 1}
        self.assertTrue(self.mod.grava(linha))
        self.assertFalse(self.mod.grava(linha))
        self.assertTrue(self.mod.grava(dict(linha, x=2)))
        gravadas = self.linhas()
        self.assertEqual(len(gravadas), 2)
        self.assertIn("gerado_em", gravadas[0])

    def test_sem_credencial_exit_2_e_linha_do_disco_gravada(self):
        self.mod.cloudflare_auth.ambiente = lambda caminho=None: {}
        codigo = self.mod.main(["--dia", DIA.isoformat()])
        self.assertEqual(codigo, 2)
        gravadas = self.linhas()
        self.assertEqual(len(gravadas), 1)
        linha = gravadas[0]
        self.assertFalse(linha["graphql_disponivel"])
        self.assertEqual(linha["motivo_graphql"], "sem_credencial")
        self.assertEqual(linha["misses_pre_head_sem_purga"]["total"], 50)
        self.assertEqual(linha["purgas_tudo"], 1)
        self.assertAlmostEqual(linha["share_autoaquecimento"]["share"], 0.4)
        self.assertAlmostEqual(linha["travessia_por_bot"]["bingbot"]["travessia"], 292 / 450, places=4)
        self.assertNotIn("cache_status", linha)

    def test_com_graphql_injetado_exit_0_e_dias_iterados(self):
        self.mod.cloudflare_auth.ambiente = lambda caminho=None: {"CLOUDFLARE_ZONE_TOKEN": "t", "CLOUDFLARE_ZONE_ID": "z"}
        self.mod.GRAPHQL = graphql_falso
        self.mod.RESOLVER_ZONA = lambda env: ("z", None)
        codigo = self.mod.main(["--dia", DIA.isoformat(), "--dias", "2"])
        self.assertEqual(codigo, 0, "exit 2 aqui é GraphQL não medido — veja "
                                    "test_a_janela_da_bancada_cabe_na_retencao")
        gravadas = self.linhas()
        self.assertEqual([l["date"] for l in gravadas],
                         [(DIA - dt.timedelta(days=1)).isoformat(), DIA.isoformat()])
        self.assertTrue(all(l["graphql_disponivel"] for l in gravadas))
        self.assertEqual(gravadas[1]["misses_do_aquecedor"]["requests"], 1000)
        self.assertEqual(gravadas[1]["cache_status"]["por_status"]["miss"]["requests"], 4032)
        self.assertEqual(gravadas[1]["conferencia_exata"]["requests_1d"], 9700)
        # segunda execução idêntica: nada regravado
        self.assertEqual(self.mod.main(["--dia", DIA.isoformat(), "--dias", "2"]), 0)
        self.assertEqual(len(self.linhas()), 2)

    def test_dia_alem_da_retencao_marca_motivo_e_exit_2(self):
        self.mod.cloudflare_auth.ambiente = lambda caminho=None: {"CLOUDFLARE_ZONE_TOKEN": "t"}
        self.mod.RESOLVER_ZONA = lambda env: ("z", None)
        self.mod.GRAPHQL = lambda consulta, variaveis, **kw: (resposta([]), "")
        antigo = (dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=30)).isoformat()
        self.assertEqual(self.mod.main(["--dia", antigo]), 2)
        self.assertEqual(self.linhas()[0]["motivo_graphql"], "fora_da_retencao")


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]] + sys.argv[1:])
