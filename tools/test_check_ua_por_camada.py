#!/usr/bin/env python3
"""Testes de UA por alvo/camada -- tools/check-what-bots-see,
tools/check-what-bots-see-externo e tools/check-superficie-bots-live.

POR QUE EXISTE (2026-09-03). O contrato do dono (CLAUDE.md) e tolerancia
zero: "PROIBIDO self-warming/requests com User-Agent de bots reais (GPTBot,
ClaudeBot, etc.) -- FRAUDE". Ate esta data, tools/check-what-bots-see em modo
--borda mandava o MESMO UA de Googlebot/GPTBot/PerplexityBot/etc. da tabela
PERFIS contra o dominio publico -- a Cloudflare le esse UA como visita
legitima do robo, mesmo com X-Bot-Simulation: true (a borda NAO le esse
cabecalho, so a origem le -- ver internal/httpserver/access_log.go). Este
teste trava a regra sem rede: a funcao que decide User-Agent e cabecalhos
nunca devolve identidade de bot real fora de 127.0.0.1, em nenhuma das tres
ferramentas que tocam a borda.

tools/check-what-bots-see-externo e tools/check-superficie-bots-live NAO
precisaram de correcao de UA (ja usavam so identidade propria em toda
camada) -- os testes aqui travam essa garantia como REGRESSAO, nao como
correcao.

Sem rede: as tres funcoes testadas sao puras (recebem o alvo, devolvem
argv/headers) -- nenhum teste aqui abre socket. Padrao de import de script
sem extensao .py replicado de tools/test_check_superficie_bots_live.py.
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import unittest

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))

# Fragmentos que identificam UA de bot REAL nas tabelas das tres ferramentas
# (PERFIS de check-what-bots-see). Qualquer um destes aparecendo num
# argv/UA/header enderecado a um alvo REMOTO e a fraude que este teste existe
# para pegar.
FRAGMENTOS_DE_BOT_REAL = (
    "Googlebot", "bingbot", "GPTBot", "ChatGPT-User", "OAI-SearchBot",
    "Claude-SearchBot", "Claude-User", "PerplexityBot", "DuckDuckBot",
    "Applebot", "YandexBot", "Google-InspectionTool",
)

ALVO_BORDA = "https://wikijuridica.com.br"
ALVO_ORIGEM_NGINX = "http://127.0.0.1:8088"
ALVO_ORIGEM_GO = "http://127.0.0.1:8089"


def _carregar(nome_arquivo: str, nome_modulo: str):
    caminho = os.path.join(TOOLS_DIR, nome_arquivo)
    loader = importlib.machinery.SourceFileLoader(nome_modulo, caminho)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


class CheckWhatBotsSeeCabecalhosTest(unittest.TestCase):
    """tools/check-what-bots-see: cabecalhos_para(host, nome_perfil, ua_real).

    Este e o arquivo que TINHA o defeito (--borda usava UA real da tabela
    PERFIS contra o dominio publico): os casos abaixo travam a correcao."""

    @classmethod
    def setUpClass(cls):
        cls.modulo = _carregar("check-what-bots-see", "check_what_bots_see_under_test")

    def test_alvo_remoto_nunca_devolve_ua_de_bot_real(self):
        # NAO checa por fragmento generico de nome de bot: o design PEDE que o
        # perfil simulado viaje no sufixo "(simula: <nome>)" (ex.: "bingbot"),
        # entao um grep ingenuo por "bingbot" acharia falso positivo no proprio
        # UA seguro. O que importa e a string CRUA do bot (o UA real inteiro,
        # com o padrao "compatible; X/versao" que a Cloudflare autentica)
        # nunca sair, e o formato do UA proprio ser sempre o mesmo molde.
        for nome, ua_real, _classe in self.modulo.PERFIS:
            with self.subTest(perfil=nome):
                ua, _headers = self.modulo.cabecalhos_para(ALVO_BORDA, nome, ua_real)
                self.assertNotEqual(ua, ua_real)
                self.assertNotIn(ua_real, ua)
                self.assertEqual(ua, "wikijuridica-superficie-probe/1.0 (simula: %s)" % nome)
                self.assertNotIn("compatible;", ua)

    def test_alvo_remoto_marca_warming_e_bot_simulation(self):
        for nome, ua_real, _classe in self.modulo.PERFIS:
            with self.subTest(perfil=nome):
                _ua, headers = self.modulo.cabecalhos_para(ALVO_BORDA, nome, ua_real)
                self.assertEqual(headers.get("X-Warming-Request"), "true")
                self.assertEqual(headers.get("X-Bot-Simulation"), "true")

    def test_alvo_local_devolve_ua_do_bot_com_x_bot_simulation(self):
        for host_local in (ALVO_ORIGEM_NGINX, ALVO_ORIGEM_GO):
            for nome, ua_real, _classe in self.modulo.PERFIS:
                with self.subTest(host=host_local, perfil=nome):
                    ua, headers = self.modulo.cabecalhos_para(host_local, nome, ua_real)
                    self.assertEqual(ua, ua_real)
                    self.assertEqual(headers.get("X-Bot-Simulation"), "true")

    def test_x_bot_simulation_e_sempre_o_literal_true_nunca_o_nome_do_bot(self):
        # internal/httpserver/access_log.go:isWarmingRequest faz EqualFold
        # exato com "true". Se o valor virasse o nome do bot, a origem
        # gravaria bot_simulation=false numa requisicao que, contra a borda,
        # pode atravessar um MISS de cache e chegar la -- contaminando o
        # proprio ledger de trafego real que o cabecalho existe para blindar.
        for nome, ua_real, _classe in self.modulo.PERFIS:
            for alvo in (ALVO_BORDA, ALVO_ORIGEM_NGINX, ALVO_ORIGEM_GO):
                _ua, headers = self.modulo.cabecalhos_para(alvo, nome, ua_real)
                self.assertEqual(headers.get("X-Bot-Simulation"), "true")

    def test_decisao_e_pelo_host_no_alvo_explicito_tambem(self):
        # --host https://... (sem --borda) tem de ficar tao seguro quanto
        # --borda: a funcao decide por eh_local(host), nunca por uma flag.
        # Usa um dominio remoto QUALQUER, diferente do dominio publico
        # conhecido, para provar que a regra e "nao e 127.0.0.1", nao uma
        # lista fixa de hosts.
        nome, ua_real, _classe = next(p for p in self.modulo.PERFIS if p[0] == "googlebot-desktop")
        ua_via_host_remoto, headers = self.modulo.cabecalhos_para(
            "https://outro-dominio.example", nome, ua_real)
        self.assertNotEqual(ua_via_host_remoto, ua_real)
        self.assertNotIn(ua_real, ua_via_host_remoto)
        self.assertEqual(headers.get("X-Warming-Request"), "true")


class CheckWhatBotsSeeExternoArgvTest(unittest.TestCase):
    """tools/check-what-bots-see-externo: montar_comando(url, host, timeout).

    Este arquivo NUNCA teve UA de bot real -- o teste trava isso como
    regressao, nao como correcao (confirmado por leitura em 2026-09-03)."""

    @classmethod
    def setUpClass(cls):
        cls.modulo = _carregar("check-what-bots-see-externo",
                                "check_what_bots_see_externo_under_test")

    def test_argv_nunca_carrega_ua_de_bot_real_para_nenhum_alvo(self):
        urls = (
            self.modulo.PUBLICO + "/",
            self.modulo.PUBLICO + "/robots.txt",
            "http://127.0.0.1:8088/",
        )
        for url in urls:
            with self.subTest(url=url):
                cmd = self.modulo.montar_comando(url)
                texto = " ".join(cmd)
                for frag in FRAGMENTOS_DE_BOT_REAL:
                    self.assertNotIn(frag, texto)
                self.assertIn(self.modulo.UA, cmd)

    def test_argv_usa_o_mesmo_ua_proprio_com_e_sem_host_explicito(self):
        sem_host = self.modulo.montar_comando(self.modulo.PUBLICO + "/")
        com_host = self.modulo.montar_comando(
            f"http://127.0.0.1:8088/", host=self.modulo.HOST)
        self.assertIn(self.modulo.UA, sem_host)
        self.assertIn(self.modulo.UA, com_host)
        self.assertIn("X-Bot-Simulation: true", com_host)


class CheckSuperficieBotsLiveArgvTest(unittest.TestCase):
    """tools/check-superficie-bots-live: _montar_comando(base, rota, accept, camada).

    Idem: ja usava UA proprio nas tres camadas antes desta revisao; o teste
    trava isso como regressao."""

    @classmethod
    def setUpClass(cls):
        cls.modulo = _carregar("check-superficie-bots-live",
                                "check_superficie_bots_live_under_test_ua")

    def test_argv_usa_ua_proprio_nas_tres_camadas_inclusive_borda(self):
        for camada, base in self.modulo.CAMADAS.items():
            with self.subTest(camada=camada):
                cmd = self.modulo._montar_comando(base, "/", None, camada)
                texto = " ".join(cmd)
                for frag in FRAGMENTOS_DE_BOT_REAL:
                    self.assertNotIn(frag, texto)
                self.assertIn(self.modulo.UA, cmd)
                self.assertIn("X-Warming-Request: true", texto)

    def test_camada_borda_nao_manda_host_header_as_outras_mandam(self):
        cmd_borda = self.modulo._montar_comando(
            self.modulo.CAMADAS["borda"], "/", None, "borda")
        cmd_nginx = self.modulo._montar_comando(
            self.modulo.CAMADAS["nginx"], "/", None, "nginx")
        self.assertNotIn(f"Host: {self.modulo.HOST}", " ".join(cmd_borda))
        self.assertIn(f"Host: {self.modulo.HOST}", " ".join(cmd_nginx))


if __name__ == "__main__":
    unittest.main()
