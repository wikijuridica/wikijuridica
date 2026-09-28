#!/usr/bin/env python3
"""Testes de tools/generate-evento-unificado — o evento humano+bot por (dia, página).

Fixtures REAIS (nunca sintéticas, como manda CLAUDE.md "ZERO FAKE"):
`tools/testdata/evento_unificado/access-2026-09-07.jsonl` são 300 linhas
copiadas de `data/ops/access/access-2026-09-07.jsonl` (misturando as três
classes de bot observadas naquele dia e uma amostra real de linhas
`warming:true`), e `edge_bot_agents_daily-2026-09-07.jsonl` são 20 linhas
copiadas de `data/ops/edge_bot_agents_daily.jsonl` para o mesmo dia. Os testes
rodam o produtor de verdade (subprocess, como `test_check_crawl_coverage_stall.py`
já faz para ferramenta sem extensão `.py`) contra uma raiz temporária montada
com essas fixtures — nunca contra o repositório real.

Rodar:
    python3 tools/test_evento_unificado.py
"""
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
FERRAMENTA = RAIZ / "tools" / "generate-evento-unificado"
FIXTURES = RAIZ / "tools" / "testdata" / "evento_unificado"
ACCESS_FIXTURE = FIXTURES / "access-2026-09-07.jsonl"
EDGE_FIXTURE = FIXTURES / "edge_bot_agents_daily-2026-09-07.jsonl"

DIA = "2026-09-07"


def montar_raiz(tmp, dia_access=DIA, linhas_edge=None):
    """Monta data/ops/access/access-<dia>.jsonl e data/ops/edge_bot_agents_daily.jsonl
    dentro de uma raiz temporária, a partir das fixtures reais."""
    tmp = pathlib.Path(tmp)
    (tmp / "data" / "ops" / "access").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ACCESS_FIXTURE, tmp / "data" / "ops" / "access" / ("access-%s.jsonl" % dia_access))
    destino_edge = tmp / "data" / "ops" / "edge_bot_agents_daily.jsonl"
    if linhas_edge is None:
        shutil.copyfile(EDGE_FIXTURE, destino_edge)
    else:
        with open(destino_edge, "w", encoding="utf-8") as handle:
            for linha in linhas_edge:
                handle.write(linha + "\n")
    return tmp


def roda(root, *args, checar=True):
    resultado = subprocess.run(
        [sys.executable, str(FERRAMENTA), "--root", str(root), *args],
        capture_output=True, text=True, timeout=60)
    if checar and resultado.returncode != 0:
        raise AssertionError(
            "generate-evento-unificado saiu com %d\nstdout:\n%s\nstderr:\n%s"
            % (resultado.returncode, resultado.stdout, resultado.stderr))
    if checar and "--dry-run" not in args and "0 processado(s)" in resultado.stdout:
        # A JANELA PADRÃO É DE 3 DIAS E A FIXTURE É DATADA.
        #
        # `--dias` vale 3 por padrão, então a janela é `hoje-2..hoje`: a
        # fixture de 2026-09-07 saiu dela em 2026-09-10 e o produtor passou a
        # sair com 0 dia processado e exit 0 — comportamento CERTO dele. O que
        # estava errado era o teste, que lia o arquivo do dia logo depois e
        # quebrava com FileNotFoundError apontando para /tmp, escondendo a
        # causa. Três casos de TesteIdentidadePorAgente chamavam `roda(raiz)`
        # sem `--desde`, enquanto os nove que passavam já mandavam
        # `roda(root, "--desde", DIA)`.
        #
        # Esta guarda existe para que o próximo teste que esquecer o `--desde`
        # falhe DIZENDO isso, em vez de apontar para um caminho temporário que
        # ninguém consegue ler depois.
        raise AssertionError(
            "generate-evento-unificado não processou nenhum dia: a fixture é de "
            "%s e a janela padrão é de 3 dias — passe `--desde %s`.\nstdout:\n%s"
            % (DIA, DIA, resultado.stdout))
    return resultado


def le_eventos(root, dia=DIA):
    caminho = pathlib.Path(root) / "data" / "ops" / "eventos" / ("eventos-%s.jsonl" % dia)
    linhas = []
    with open(caminho, encoding="utf-8") as handle:
        for bruto in handle:
            bruto = bruto.strip()
            if bruto:
                linhas.append(json.loads(bruto))
    return linhas


def le_cursor(root):
    caminho = pathlib.Path(root) / "data" / "ops" / "eventos" / "cursor.json"
    with open(caminho, encoding="utf-8") as handle:
        return json.load(handle)


def linhas_fixture_access():
    registros = []
    with open(ACCESS_FIXTURE, encoding="utf-8") as handle:
        for bruto in handle:
            bruto = bruto.strip()
            if bruto:
                registros.append(json.loads(bruto))
    return registros


class TesteWarmingESimulacaoNaoContam(unittest.TestCase):
    """(1) Linha com warming:true ou bot_simulation:true nunca entra em
    `requisicoes` — a mesma regra de `accessledger.linhas_saneadas`."""

    def test_soma_bate_com_filtro_independente(self):
        registros = linhas_fixture_access()
        esperado_contadas = sum(
            1 for r in registros
            if not r.get("warming") and not r.get("bot_simulation"))
        esperado_warming = sum(1 for r in registros if r.get("warming"))
        esperado_simulacao = sum(1 for r in registros if r.get("bot_simulation"))
        self.assertGreater(esperado_warming, 0, "fixture precisa ter linha warming real")

        with tempfile.TemporaryDirectory() as tmp:
            root = montar_raiz(tmp)
            roda(root, "--desde", DIA)
            linhas = le_eventos(root)
            linha_dia = [l for l in linhas if l["path"] == "_dia"][0]
            soma_por_path = sum(l["requisicoes"] for l in linhas if l["path"] != "_dia")

            self.assertEqual(soma_por_path, esperado_contadas)
            self.assertEqual(linha_dia["origem_descontado_warming"], esperado_warming)
            self.assertEqual(linha_dia["origem_descontado_simulacao"], esperado_simulacao)
            self.assertEqual(linha_dia["requisicoes_liquidas"], esperado_contadas)


class TesteIdempotencia(unittest.TestCase):
    """(2) Rodar duas vezes sem dado novo não altera nenhum arquivo — bytes
    idênticos, não apenas conteúdo logicamente equivalente."""

    def test_bytes_identicos_na_segunda_execucao(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = montar_raiz(tmp)
            roda(root, "--desde", DIA)
            caminho_evento = pathlib.Path(root) / "data" / "ops" / "eventos" / ("eventos-%s.jsonl" % DIA)
            caminho_cursor = pathlib.Path(root) / "data" / "ops" / "eventos" / "cursor.json"
            bytes_evento_1 = caminho_evento.read_bytes()
            bytes_cursor_1 = caminho_cursor.read_bytes()

            roda(root, "--desde", DIA)
            bytes_evento_2 = caminho_evento.read_bytes()
            bytes_cursor_2 = caminho_cursor.read_bytes()

            self.assertEqual(bytes_evento_1, bytes_evento_2)
            self.assertEqual(bytes_cursor_1, bytes_cursor_2)


class TesteCursorAvancaSemRegredir(unittest.TestCase):
    """(3) `ultimo_dia_fechado` avança quando um dia fecha, e nunca regride —
    nem quando um `--desde` mais antigo é reprocessado depois."""

    def test_avanca_e_depois_nao_regride(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = montar_raiz(tmp)
            roda(root, "--desde", DIA)
            cursor1 = le_cursor(root)
            self.assertEqual(cursor1["ultimo_dia_fechado"], DIA)

            dia_antigo = "2026-09-01"
            shutil.copyfile(
                ACCESS_FIXTURE,
                pathlib.Path(root) / "data" / "ops" / "access" / ("access-%s.jsonl" % dia_antigo))
            roda(root, "--desde", dia_antigo)
            cursor2 = le_cursor(root)
            self.assertEqual(cursor2["ultimo_dia_fechado"], DIA,
                              "cursor regrediu para um dia mais antigo que ja tinha fechado")


class TesteGA4Indisponivel(unittest.TestCase):
    """(4) A linha `_dia` declara GA4 indisponível com motivo — nunca zero
    fingindo medição (não há credencial da GA4 Data API neste repositório)."""

    def test_bloco_ga4_disponivel_falso_com_motivo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = montar_raiz(tmp)
            roda(root, "--desde", DIA)
            linha_dia = [l for l in le_eventos(root) if l["path"] == "_dia"][0]
            self.assertIn("ga4", linha_dia)
            self.assertFalse(linha_dia["ga4"]["disponivel"])
            self.assertTrue(linha_dia["ga4"]["motivo"])


class TesteJoinComBordaUsaUltimaLinha(unittest.TestCase):
    """(5) O join por dia com a série de borda usa a ÚLTIMA linha por
    (date, agent_key) — mesma convenção de `edgetelemetry.serie_saneada`."""

    def test_ultima_linha_do_par_date_agent_key_vence(self):
        with open(EDGE_FIXTURE, encoding="utf-8") as handle:
            primeira_bruta = handle.readline().strip()
        base = json.loads(primeira_bruta)
        self.assertEqual(base["date"], DIA)
        agente = base["agent_key"]

        antiga = dict(base, authenticity="cloudflare_verified_bot_category")
        nova = dict(base, authenticity="ip_range_at_edge")
        nova["requests_sampled_ip_range"] = max(1, int(nova.get("requests_sampled") or 1))
        nova["requests_sampled_cloudflare_verified"] = 0

        with tempfile.TemporaryDirectory() as tmp:
            root = montar_raiz(tmp, linhas_edge=[
                json.dumps(antiga, ensure_ascii=False),
                json.dumps(nova, ensure_ascii=False),
            ])
            roda(root, "--desde", DIA)
            linha_dia = [l for l in le_eventos(root) if l["path"] == "_dia"][0]
            self.assertIn(agente, linha_dia["borda_por_agente"])
            self.assertEqual(
                linha_dia["borda_por_agente"][agente]["authenticity"], "ip_range_at_edge")


class TesteDryRunNaoEscreve(unittest.TestCase):
    """--dry-run calcula mas não grava nada em disco."""

    def test_dry_run_nao_cria_arquivo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = montar_raiz(tmp)
            roda(root, "--desde", DIA, "--dry-run")
            caminho_evento = pathlib.Path(root) / "data" / "ops" / "eventos" / ("eventos-%s.jsonl" % DIA)
            self.assertFalse(caminho_evento.exists())


class TesteFerramentaMCPNoEvento(unittest.TestCase):
    """POST /mcp com mcp_tool no ledger vira contagem por ferramenta e por agente."""

    def test_por_ferramenta_mcp(self):
        import json, os, subprocess, sys, tempfile
        raiz = tempfile.mkdtemp(prefix="evento-mcp-")
        os.makedirs(os.path.join(raiz, "data", "ops", "access"))
        linhas = [
            {"ts": "2026-09-07T10:00:00Z", "method": "POST", "path": "/mcp", "status": 200, "bytes": 100, "duration_ms": 5,
             "route_class": "mcp", "bot_class": "unknown_or_standard_user_agent", "bot_rule": "*",
             "user_agent": "Mozilla/5.0 (compatible; GPTBot/1.0; +https://openai.com/gptbot)", "warming": False, "bot_simulation": False,
             "mcp_method": "tools/call", "mcp_tool": "contexto_juridico"},
            {"ts": "2026-09-07T10:00:01Z", "method": "POST", "path": "/mcp", "status": 200, "bytes": 100, "duration_ms": 5,
             "route_class": "mcp", "bot_class": "unknown_or_standard_user_agent", "bot_rule": "*",
             "user_agent": "Mozilla/5.0 (compatible; GPTBot/1.0; +https://openai.com/gptbot)", "warming": False, "bot_simulation": False,
             "mcp_method": "tools/list"},
            {"ts": "2026-09-07T10:00:02Z", "method": "POST", "path": "/mcp", "status": 200, "bytes": 100, "duration_ms": 5,
             "route_class": "mcp", "bot_class": "unknown_or_standard_user_agent", "bot_rule": "*",
             "user_agent": "curl/8", "warming": True, "bot_simulation": False, "mcp_method": "tools/call", "mcp_tool": "contexto_juridico"},
            {"ts": "2026-09-07T10:00:03Z", "method": "POST", "path": "/mcp", "status": 200, "bytes": 100, "duration_ms": 5,
             "route_class": "mcp", "bot_class": "unknown_or_standard_user_agent", "bot_rule": "*",
             "user_agent": "agente-x/1.0", "warming": False, "bot_simulation": False, "mcp_method": "tools/call", "mcp_tool": "ler_pagina",
             "oauth_client": "wj_cliente_abc"},
        ]
        with open(os.path.join(raiz, "data", "ops", "access", "access-2026-09-07.jsonl"), "w") as f:
            for l in linhas:
                f.write(json.dumps(l) + "\n")
        ferramenta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "generate-evento-unificado")
        r = subprocess.run([sys.executable, ferramenta, "--root", raiz, "--desde", "2026-09-07", "--dias", "1"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        eventos = [json.loads(l) for l in open(os.path.join(raiz, "data", "ops", "eventos", "eventos-2026-09-07.jsonl"))]
        mcp = [e for e in eventos if e["path"] == "/mcp"][0]
        self.assertEqual(mcp["por_ferramenta_mcp"], {"contexto_juridico": 1, "ler_pagina": 1}, "o aquecimento nao conta")
        self.assertEqual(mcp["por_metodo_mcp"], {"tools/list": 1})
        self.assertEqual(sorted(mcp["por_ferramenta_mcp_agente"].keys()), ["contexto_juridico|gptbot", "ler_pagina|humano_ou_nao_identificado"])
        self.assertEqual(mcp["por_cliente_oauth"], {"wj_cliente_abc": 1}, "cliente identificado por Bearer conta uma vez")




def agentes_de_ia_da_ferramenta():
    """Le AGENTES_DE_IA do proprio produtor (arquivo sem .py), para o teste
    conferir com a MESMA lista, nunca com uma copia."""
    import importlib.machinery
    import importlib.util
    loader = importlib.machinery.SourceFileLoader("gevu", str(FERRAMENTA))
    spec = importlib.util.spec_from_loader("gevu", loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo.AGENTES_DE_IA


class TesteIdentidadePorAgente(unittest.TestCase):
    """`identidade_por_agente` na linha `_dia`: por agent_key, quantas linhas do
    ledger do nginx cairam em cada `ip_verificacao` — conferido por um filtro
    independente sobre a MESMA fixture real (nginx-2026-09-07.jsonl, 8 linhas
    `forged` reais do bingbot + autenticas + amostra por stride). Motivo medido
    em 2026-09-08: um scanner trocava o UA a cada requisicao (GPTBot,
    Claude-User, PerplexityBot...) e a contagem por UA o somava como agente."""

    NGINX_FIXTURE = FIXTURES / "nginx-2026-09-07.jsonl"

    FAIXAS_REAIS = RAIZ / "data" / "ops" / "bot_ip_ranges"

    def _raiz_com_nginx(self, tmp, com_faixas=True):
        raiz = montar_raiz(tmp)
        shutil.copyfile(self.NGINX_FIXTURE, raiz / "data" / "ops" / "access" / ("nginx-%s.jsonl" % DIA))
        if com_faixas:
            shutil.copytree(self.FAIXAS_REAIS, raiz / "data" / "ops" / "bot_ip_ranges")
        return raiz

    def test_linha_do_acervo_e_conferida_pelo_consumidor(self):
        """No acervo o ledger deixa o IP em claro e sem veredito; o evento e quem
        confere contra data/ops/bot_ip_ranges. Com as faixas reais, nenhuma linha
        de agente com faixa publicada pode sobrar em nao_verificado; sem as
        faixas, todas sobram — e o bloco diz quantas conferiu."""
        with tempfile.TemporaryDirectory() as tmp:
            raiz = self._raiz_com_nginx(tmp)
            roda(raiz, "--desde", DIA)
            bloco = [e for e in le_eventos(raiz) if e["path"] == "_dia"][0]["identidade_por_agente"]
            self.assertGreater(bloco["conferidas_pelo_consumidor"], 0)
            for agente in ("oai-searchbot", "perplexitybot", "gptbot"):
                if agente in bloco["por_agente"]:
                    self.assertEqual(bloco["por_agente"][agente]["nao_verificado"], 0, agente)
        with tempfile.TemporaryDirectory() as tmp:
            raiz = self._raiz_com_nginx(tmp, com_faixas=False)
            roda(raiz, "--desde", DIA)
            bloco = [e for e in le_eventos(raiz) if e["path"] == "_dia"][0]["identidade_por_agente"]
            # Sem faixas o consumidor ainda confere, mas so pode dizer
            # "unverifiable": nenhuma linha do acervo vira forged nem authentic.
            forjados_do_ledger = 8  # linhas `forged` reais do bingbot ja carimbadas pelo ledger social
            self.assertEqual(sum(v["forged"] for v in bloco["por_agente"].values()), forjados_do_ledger)
            self.assertEqual(sum(v["nao_verificado"] for v in bloco["por_agente"].values()), 0)

    def test_bloco_bate_com_filtro_independente(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = self._raiz_com_nginx(tmp)
            roda(raiz, "--desde", DIA)
            dia = [e for e in le_eventos(raiz) if e["path"] == "_dia"][0]
            bloco = dia["identidade_por_agente"]
            self.assertTrue(bloco["disponivel"])
            esperado = {}
            forjados = 0
            sys.path.insert(0, str(RAIZ / "tools"))
            import botagents  # noqa: E402
            faixas = botagents.ler_faixas(str(raiz))
            with open(self.NGINX_FIXTURE, encoding="utf-8") as handle:
                for bruto in handle:
                    r = json.loads(bruto)
                    if r.get("warming") or r.get("bot_simulation") or not r.get("agent_key"):
                        continue
                    b = r.get("ip_verificacao")
                    if not b and r.get("remote_addr_forma") == "ip" and r.get("remote_addr"):
                        redes = faixas.get(r["agent_key"].strip().lower())
                        b = ("authentic" if botagents.em_faixa(r["remote_addr"], redes) else "forged") if redes else "unverifiable"
                    b = b or "nao_verificado"
                    esperado.setdefault(r["agent_key"], {"authentic": 0, "forged": 0, "unverifiable": 0, "nao_verificado": 0})[b] += 1
                    if b == "forged" and r["agent_key"] in agentes_de_ia_da_ferramenta():
                        forjados += 1
            # Com faixas na raiz, o consumidor confere as linhas do acervo: o
            # TOTAL por agente tem de bater; a distribuicao entre buckets e o
            # que o teste seguinte prova.
            self.assertEqual({a: sum(v.values()) for a, v in bloco["por_agente"].items()},
                             {a: sum(v.values()) for a, v in esperado.items()})
            self.assertEqual({a: v["forged"] for a, v in bloco["por_agente"].items() if v["forged"]},
                             {a: v["forged"] for a, v in esperado.items() if v["forged"]})
            self.assertGreater(sum(v["forged"] for v in esperado.values()), 0, "a fixture precisa ter linhas forged reais")
            self.assertEqual(bloco["agentes_de_ia_forjados"], forjados)

    def test_sem_ledger_do_nginx_declara_indisponivel(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = montar_raiz(tmp)
            roda(raiz, "--desde", DIA)
            dia = [e for e in le_eventos(raiz) if e["path"] == "_dia"][0]
            self.assertFalse(dia["identidade_por_agente"]["disponivel"])
            self.assertIn("motivo", dia["identidade_por_agente"])



def carrega_modulo():
    """Importa o gerador como módulo (o arquivo não tem sufixo .py) para testar
    funções puras sem subprocesso."""
    import importlib.machinery
    import importlib.util
    caminho = str(pathlib.Path(__file__).resolve().parent / "generate-evento-unificado")
    loader = importlib.machinery.SourceFileLoader("generate_evento_unificado", caminho)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


class TestCompactaClarity(unittest.TestCase):
    """A linha por URL entra compacta (derivado), a linha por Device entra inteira.
    Mutante: sem `compacta_clarity` na montagem, `metricas` volta a aparecer."""

    def test_url_entra_so_com_derivado(self):
        mod = carrega_modulo()
        cru = {"schema": "clarity_insights_v1", "coletado_em": "2026-09-09T14:33:00+00:00",
               "dimensoes": ["URL"], "metricas": [{"metricName": "Traffic", "information": [{"Url": "/x/"}] * 500}],
               "top_urls": [{"url": "/x/", "sessoes": 3}], "derivacao_urls": {"paths_distintos": 1}}
        compacta = mod.compacta_clarity(cru)
        self.assertNotIn("metricas", compacta)
        self.assertEqual(compacta["top_urls"], cru["top_urls"])
        self.assertIn("metricas_omitidas", compacta)
        device = {"schema": "clarity_insights_v1", "coletado_em": "2026-09-09T09:15:00+00:00",
                  "dimensoes": ["Device"], "metricas": [{"metricName": "DeadClickCount"}]}
        self.assertIs(mod.compacta_clarity(device), device)

    def test_linha_do_dia_nao_carrega_o_cru(self):
        mod = carrega_modulo()
        cru = {"schema": "clarity_insights_v1", "coletado_em": "2026-09-09T14:33:00+00:00",
               "dimensoes": ["URL"], "metricas": [{"grande": "x" * 1000}], "top_urls": []}
        resumo = {"origem_total": 0, "origem_descontado_quarentena": 0, "origem_descontado_warming": 0,
                  "origem_descontado_simulacao": 0, "linhas_invalidas": 0}
        linha = mod.montar_linha_dia_agregada("2026-09-09", resumo, {}, [cru])
        self.assertTrue(linha["clarity"]["disponivel"])
        self.assertNotIn("metricas", linha["clarity"]["coletas"][0])


if __name__ == "__main__":
    unittest.main()
