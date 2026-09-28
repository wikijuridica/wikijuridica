#!/usr/bin/env python3
"""Testes de report-access-traffic e check-metrics-endpoint.

O teste central aqui é ANTI-INFLAÇÃO DE MÉTRICA. O contrato do projeto proíbe
inflar analytics e exige que a medição reflita apenas tráfego real; um relatório
que contasse rastreador de SEO como gente estaria mentindo para o dono sobre a
audiência do portal.

O detalhe que torna isso não-óbvio: praticamente TODO crawler comercial
(AhrefsBot, SemrushBot, MJ12bot, DotBot, Bytespider) carrega "Mozilla/5.0" no
User-Agent. Um critério ingênuo de "tem Mozilla/ e o nginx não marcou como bot"
classificaria os cinco como navegador — e ninguém perceberia, porque esses bots
não estão nos maps do nginx nem em content/crawl_policy.json.

Rodar:
    python3 tools/test_report_access_traffic.py
    python3 -m unittest discover -s tools -p 'test_report_access_traffic.py'
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
RELATORIO = RAIZ / "tools" / "report-access-traffic"
CHECK_METRICAS = RAIZ / "tools" / "check-metrics-endpoint"
POLITICA = RAIZ / "content" / "crawl_policy.json"

LINHA = ('127.0.0.1 - [04/Aug/2026:14:18:32 -0300] host=wikijuridica.com.br '
         '"GET {rota} HTTP/1.1" {status} 5632 "{agente}" '
         'deny={deny} allow={allow} block=0 rt=0.001 cf_ray=-')

NAVEGADORES = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# Rastreadores que NÃO estão nos maps do nginx nem em crawl_policy.json e ainda
# assim se passam por navegador. São a razão de existir deste teste.
CRAWLERS_DISFARCADOS = [
    "Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)",
    "Mozilla/5.0 (compatible; SemrushBot/7~bl; +http://www.semrush.com/bot.html)",
    "Mozilla/5.0 (compatible; MJ12bot/v1.4.8; http://mj12bot.com/)",
    "Mozilla/5.0 (compatible; DotBot/1.2; +https://opensiteexplorer.org/dotbot)",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "HeadlessChrome/120.0.0.0 Safari/537.36",
    "python-requests/2.31.0",
    "Go-http-client/2.0",
]


def carregar_modulo(caminho: pathlib.Path, nome: str):
    spec = importlib.util.spec_from_loader(
        nome, importlib.machinery.SourceFileLoader(nome, str(caminho)))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def escrever_log(destino: pathlib.Path, agentes: list[str], rota: str = "/familia/divorcio/",
                 status: int = 200, deny: int = 0, allow: int = 0) -> None:
    with destino.open("w", encoding="utf-8") as arquivo:
        for agente in agentes:
            arquivo.write(LINHA.format(rota=rota, status=status, agente=agente,
                                       deny=deny, allow=allow) + "\n")


def rodar_relatorio(log: pathlib.Path) -> dict:
    processo = subprocess.run(
        [sys.executable, str(RELATORIO), "--log", str(log), "--json"],
        capture_output=True, text=True, check=False)
    if processo.returncode != 0:
        raise AssertionError(f"report-access-traffic saiu {processo.returncode}: {processo.stderr}")
    return json.loads(processo.stdout)


class TestContagemDeTrafegoHumano(unittest.TestCase):
    """A contagem não pode inflar: robô disfarçado nunca entra como navegador."""

    def test_crawler_disfarcado_de_navegador_nao_conta_como_navegador(self):
        with tempfile.TemporaryDirectory() as pasta:
            log = pathlib.Path(pasta) / "access.log"
            escrever_log(log, CRAWLERS_DISFARCADOS)
            relatorio = rodar_relatorio(log)
            self.assertEqual(relatorio["requisicoes"], len(CRAWLERS_DISFARCADOS))
            self.assertEqual(
                relatorio["requisicoes_navegador_sem_marca_de_robo"], 0,
                "rastreador comercial foi contado como navegador — métrica inflada")

    def test_navegador_real_conta(self):
        with tempfile.TemporaryDirectory() as pasta:
            log = pathlib.Path(pasta) / "access.log"
            escrever_log(log, NAVEGADORES)
            relatorio = rodar_relatorio(log)
            self.assertEqual(
                relatorio["requisicoes_navegador_sem_marca_de_robo"], len(NAVEGADORES),
                "navegador real deixou de ser contado — o filtro ficou estrito demais")

    def test_mistura_conta_apenas_os_navegadores(self):
        with tempfile.TemporaryDirectory() as pasta:
            log = pathlib.Path(pasta) / "access.log"
            escrever_log(log, NAVEGADORES + CRAWLERS_DISFARCADOS)
            relatorio = rodar_relatorio(log)
            self.assertEqual(relatorio["requisicoes"],
                             len(NAVEGADORES) + len(CRAWLERS_DISFARCADOS))
            self.assertEqual(
                relatorio["requisicoes_navegador_sem_marca_de_robo"], len(NAVEGADORES))

    def test_bot_marcado_pelo_nginx_nao_conta(self):
        """Bot já marcado no ingress (deny=1) nunca entra na conta."""
        with tempfile.TemporaryDirectory() as pasta:
            log = pathlib.Path(pasta) / "access.log"
            escrever_log(log, NAVEGADORES, deny=1)
            relatorio = rodar_relatorio(log)
            self.assertEqual(relatorio["requisicoes_navegador_sem_marca_de_robo"], 0)
            self.assertEqual(relatorio["requisicoes_bloqueadas_no_ingress"],
                             len(NAVEGADORES))


class TestClassificadorEspelhaOServidor(unittest.TestCase):
    """A classificação tem que bater com crawl.BotAccessMatcher (Go)."""

    @classmethod
    def setUpClass(cls):
        modulo = carregar_modulo(RELATORIO, "wj_report_access_traffic")
        regras = json.loads(POLITICA.read_text(encoding="utf-8"))["access_rules"]
        cls.classificador = modulo.ClassificadorDeBot(regras)

    def test_classes_conhecidas(self):
        casos = [
            ("Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
             "valuable_search_or_user_bot"),
            ("Mozilla/5.0 (compatible; GPTBot/1.2; +https://openai.com/gptbot)",
             "training_bot"),
            ("OAI-SearchBot/1.0", "valuable_search_or_user_bot"),
            ("OAI-AdsBot/1.0", "ads_validation_bot"),
            ("Mozilla/5.0 (Windows NT 10.0) Chrome/120 Safari/537.36",
             "unknown_or_standard_user_agent"),
            ("", "unknown_or_standard_user_agent"),
        ]
        for agente, esperado in casos:
            with self.subTest(agente=agente[:40]):
                self.assertEqual(self.classificador.classificar(agente), esperado)

    def test_candidato_mais_longo_vence(self):
        """Applebot-Extended (treinamento) não pode ser lido como Applebot (busca).

        É a mesma regra do Go (userAgentTokenMatches + maior token vence). Se
        invertesse, o portal trataria um crawler de treinamento como buscador
        valioso nos relatórios.
        """
        base = "Mozilla/5.0 (Macintosh) AppleWebKit/605.1.15 "
        self.assertEqual(
            self.classificador.classificar(base + "Applebot-Extended/0.1"), "training_bot")
        self.assertEqual(
            self.classificador.classificar(base + "Applebot/0.1"),
            "valuable_search_or_user_bot")

    def test_curinga_nao_conta_como_bot_nomeado(self):
        """Cair no '*' não é o mesmo que casar um bot do registro."""
        _, casou = self.classificador.classificar_detalhado("Chrome/120 Safari/537.36")
        self.assertFalse(casou)
        _, casou_googlebot = self.classificador.classificar_detalhado("Googlebot/2.1")
        self.assertTrue(casou_googlebot)


class TestLeituraDeLog(unittest.TestCase):
    def test_log_ausente_reprova_sem_estourar(self):
        with tempfile.TemporaryDirectory() as pasta:
            ausente = pathlib.Path(pasta) / "nao-existe.log"
            processo = subprocess.run(
                [sys.executable, str(RELATORIO), "--log", str(ausente), "--json"],
                capture_output=True, text=True, check=False)
            self.assertEqual(processo.returncode, 1)
            self.assertIn("nenhum log encontrado", processo.stderr)

    def test_linha_malformada_e_contada_e_nao_derruba(self):
        with tempfile.TemporaryDirectory() as pasta:
            log = pathlib.Path(pasta) / "access.log"
            with log.open("w", encoding="utf-8") as arquivo:
                arquivo.write("linha completamente fora do formato\n")
                arquivo.write(LINHA.format(rota="/", status=200, agente=NAVEGADORES[0],
                                           deny=0, allow=0) + "\n")
            relatorio = rodar_relatorio(log)
            self.assertEqual(relatorio["requisicoes"], 2)
            self.assertEqual(relatorio["linhas_malformadas"], 1)
            self.assertEqual(relatorio["requisicoes_navegador_sem_marca_de_robo"], 1)

    def test_404_e_5xx_sao_separados_por_rota(self):
        with tempfile.TemporaryDirectory() as pasta:
            log = pathlib.Path(pasta) / "access.log"
            with log.open("w", encoding="utf-8") as arquivo:
                arquivo.write(LINHA.format(rota="/sumiu/", status=404,
                                           agente=NAVEGADORES[0], deny=0, allow=0) + "\n")
                arquivo.write(LINHA.format(rota="/quebrou/", status=503,
                                           agente=NAVEGADORES[0], deny=0, allow=0) + "\n")
            relatorio = rodar_relatorio(log)
            self.assertEqual(relatorio["rotas_404"], {"/sumiu/": 1})
            self.assertEqual(relatorio["rotas_5xx"], {"/quebrou/": 1})
            self.assertEqual(relatorio["por_classe_de_status"], {"4xx": 1, "5xx": 1})


class TestValidacaoDoFormatoPrometheus(unittest.TestCase):
    """O parser de check-metrics-endpoint precisa reprovar texto inválido."""

    @classmethod
    def setUpClass(cls):
        cls.modulo = carregar_modulo(CHECK_METRICAS, "wj_check_metrics_endpoint")

    def test_texto_valido_sem_erros(self):
        corpo = ("# HELP portal_http_requests_total Total.\n"
                 "# TYPE portal_http_requests_total counter\n"
                 'portal_http_requests_total{method="GET",status="200"} 12\n')
        analisado = self.modulo.analisar_formato(corpo)
        self.assertEqual(analisado["erros_formato"], [])
        self.assertEqual(analisado["total_amostras"], 1)
        self.assertEqual(analisado["familias"]["portal_http_requests_total"], "counter")

    def test_valor_nao_numerico_reprova(self):
        corpo = ("# TYPE portal_http_requests_total counter\n"
                 "portal_http_requests_total abacaxi\n")
        self.assertTrue(self.modulo.analisar_formato(corpo)["erros_formato"])

    def test_valores_especiais_sao_aceitos(self):
        for especial in ("NaN", "+Inf", "-Inf", "1.5e-07"):
            with self.subTest(valor=especial):
                corpo = f"# TYPE m gauge\nm {especial}\n"
                self.assertEqual(self.modulo.analisar_formato(corpo)["erros_formato"], [])

    def test_label_de_caminho_e_detectado(self):
        corpo = ("# TYPE portal_pages_served_total counter\n"
                 'portal_pages_served_total{path="/familia/divorcio/"} 4\n')
        analisado = self.modulo.analisar_formato(corpo)
        self.assertTrue(self.modulo.checar_cardinalidade(analisado))

    def test_valor_com_cara_de_caminho_e_detectado(self):
        corpo = ("# TYPE portal_pages_served_total counter\n"
                 'portal_pages_served_total{rota="/familia/divorcio/"} 4\n')
        analisado = self.modulo.analisar_formato(corpo)
        self.assertTrue(self.modulo.checar_cardinalidade(analisado))

    def test_const_label_com_barra_nao_e_falso_positivo(self):
        """module_path contém '/' e NÃO pode ser lido como caminho de URL."""
        corpo = ("# TYPE portal_http_requests_total counter\n"
                 'portal_http_requests_total{module_path="github.com/prometheus/client_golang"} 1\n')
        analisado = self.modulo.analisar_formato(corpo)
        self.assertEqual(self.modulo.checar_cardinalidade(analisado), [])

    def test_histograma_conta_como_familia_presente(self):
        corpo = ("portal_http_request_duration_seconds_bucket{le=\"1\"} 3\n"
                 "portal_http_request_duration_seconds_sum 0.5\n"
                 "portal_http_request_duration_seconds_count 3\n")
        analisado = self.modulo.analisar_formato(corpo)
        self.assertTrue(self.modulo.familia_presente(
            "portal_http_request_duration_seconds", analisado))

    def test_classe_de_bot_faltando_e_detectada(self):
        corpo = ("# TYPE portal_bot_class_requests_total counter\n"
                 'portal_bot_class_requests_total{bot_class="training_bot"} 1\n')
        analisado = self.modulo.analisar_formato(corpo)
        faltando = self.modulo.checar_classes_de_bot(analisado)
        self.assertIn("valuable_search_or_user_bot", faltando)
        self.assertNotIn("training_bot", faltando)


if __name__ == "__main__":
    unittest.main(verbosity=2)
