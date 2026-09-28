#!/usr/bin/env python3
"""test_generate_bot_agents_daily_ip_lane — prova a FASE 2 (verificação por
faixa de IP oficial) de `tools/generate-bot-agents-daily`, schema v4.

POR QUE ESTE TESTE EXISTE, com o número que obriga (medido em 2026-09-02): o
PerplexityBot faz ~1.200 requisições/dia à borda, 100% dos `clientIP` dentro
dos 8 prefixos oficiais publicados em `data/ops/bot_ip_ranges/
perplexitybot.json`, e `verifiedBotCategory` VAZIA em 100% das requisições — a
Cloudflare não verifica a Perplexity, e o schema v3 gravava
`requests_sampled=0` para um bot que rastreava todo dia de dentro da própria
faixa que ele publica. Este arquivo prova que a FASE 2 (segunda consulta por
`clientIP`, filtrada por User-Agent) reclassifica exatamente o que a faixa
oficial autentica, e SÓ isso — sem duplicar o que a Cloudflare já verificou,
sem mover tráfego local-do-Brasil que nunca esteve na perna "sem verificação",
e sem atribuir a um agente o tráfego de outro.

NÃO CHAMA A API: todos os "grupos" do GraphQL são sintéticos, no mesmo formato
que `httpRequestsAdaptiveGroups` devolve (`count`, `avg.sampleInterval`,
`dimensions.{userAgent,clientIP,clientCountryName,verifiedBotCategory}`). As
faixas de IP também são sintéticas — o teste não depende de quais arquivos
existem HOJE em `data/ops/bot_ip_ranges/`, para não quebrar quando o timer de
faixas adicionar ou remover um operador.

Uso:
    python3 -m pytest tools/test_generate_bot_agents_daily_ip_lane.py -q
    python3 tools/test_generate_bot_agents_daily_ip_lane.py
"""
import importlib.machinery
import importlib.util
import ipaddress
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.abspath(__file__))
_ALVO = os.path.join(RAIZ, "generate-bot-agents-daily")

# O produtor não tem extensão .py: sem loader explícito, spec_from_file_location
# devolve None e o import falha sem explicar por quê (mesma armadilha
# documentada em check-bot-telemetry-honesty-selftest).
sys.path.insert(0, RAIZ)
_loader = importlib.machinery.SourceFileLoader("gbad_ip_lane", _ALVO)
_spec = importlib.util.spec_from_loader("gbad_ip_lane", _loader)
gbad = importlib.util.module_from_spec(_spec)
_loader.exec_module(gbad)


def _grupo(count, ua, categoria="", pais="US", ip=None, intervalo=1.0):
    dimensoes = {"userAgent": ua, "clientCountryName": pais, "verifiedBotCategory": categoria}
    if ip is not None:
        dimensoes["clientIP"] = ip
    return {"count": count, "avg": {"sampleInterval": intervalo}, "dimensions": dimensoes}


PERPLEXITYBOT_UA = "Mozilla/5.0 (compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)"
PERPLEXITY_USER_UA = "Mozilla/5.0 (compatible; Perplexity-User/1.0; +https://perplexity.ai/perplexity-user)"
GOOGLEBOT_UA = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
YANDEXBOT_UA = "Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)"

FAIXA_PERPLEXITYBOT = [ipaddress.ip_network("18.97.9.96/29")]  # .96 - .103


class TestAcumulaPrimario(unittest.TestCase):
    def test_particao_tres_vias(self):
        grupos = [
            _grupo(26, GOOGLEBOT_UA, categoria="search_engine_crawler", pais="US"),
            _grupo(9, GOOGLEBOT_UA, categoria="", pais="BR"),  # sonda local (BR, sempre-estrangeiro)
            _grupo(532, PERPLEXITYBOT_UA, categoria="", pais="US"),  # sem verificacao nenhuma
        ]
        por_agente = gbad._acumular_primario(grupos)

        self.assertEqual(por_agente["googlebot"]["requests_sampled"], 26)
        self.assertEqual(por_agente["googlebot"]["requests_local_verification"], 9)
        self.assertEqual(por_agente["googlebot"]["requests_sampled_unverified_ua"], 0)

        self.assertEqual(por_agente["perplexitybot"]["requests_sampled"], 0)
        self.assertEqual(por_agente["perplexitybot"]["requests_sampled_unverified_ua"], 532)
        self.assertIn(PERPLEXITYBOT_UA, por_agente["perplexitybot"]["user_agents_unverified"])


class TestCandidatosIPRange(unittest.TestCase):
    def test_so_entra_quem_tem_trafego_e_faixa(self):
        grupos = [
            _grupo(26, GOOGLEBOT_UA, categoria="search_engine_crawler"),  # 100% verificado: sem candidatura
            _grupo(50, YANDEXBOT_UA, categoria=""),  # sem verificacao, mas SEM faixa oficial
            _grupo(532, PERPLEXITYBOT_UA, categoria=""),  # sem verificacao, COM faixa oficial
        ]
        por_agente = gbad._acumular_primario(grupos)
        faixas = {"perplexitybot": FAIXA_PERPLEXITYBOT}  # yandexbot deliberadamente ausente

        candidatos = gbad._candidatos_ip_range(por_agente, faixas)

        self.assertEqual(candidatos, ["perplexitybot"])


class TestTokensDeFamilia(unittest.TestCase):
    def test_extrai_grafia_real_case_sensitive(self):
        tokens = gbad._tokens_de_familia("perplexitybot", [PERPLEXITYBOT_UA])
        # A grafia REAL na amostra é "PerplexityBot" (maiúscula P e B); a API
        # da Cloudflare faz LIKE sensível a caixa (medido em 2026-09-02), então
        # o token tem que preservar essa grafia exata.
        self.assertIn("PerplexityBot", tokens)

    def test_sem_amostra_sem_token(self):
        # Amostra que não contém a marca do agente: nada para extrair.
        self.assertEqual(gbad._tokens_de_familia("perplexitybot", ["algo sem relacao nenhuma"]), [])
        self.assertEqual(gbad._tokens_de_familia("perplexitybot", []), [])


class TestFiltroOrUserAgent(unittest.TestCase):
    def test_monta_string_exata(self):
        self.assertEqual(
            gbad._filtro_or_userAgent(["PerplexityBot"]),
            'OR: [{userAgent_like: "%PerplexityBot%"}]')
        self.assertEqual(
            gbad._filtro_or_userAgent(["Googlebot", "googlebot"]),
            'OR: [{userAgent_like: "%Googlebot%"}, {userAgent_like: "%googlebot%"}]')


class TestProcessarGruposSecundarios(unittest.TestCase):
    def test_particao_por_ip_categoria_e_pais(self):
        grupos = [
            # 1) dentro da faixa oficial, sem verificacao da CF -> CONTA
            _grupo(300, PERPLEXITYBOT_UA, categoria="", ip="18.97.9.100"),
            _grupo(200, PERPLEXITYBOT_UA, categoria="", ip="18.97.9.101"),
            # 2) fora da faixa oficial -> NAO conta, fica sem verificacao
            _grupo(32, PERPLEXITYBOT_UA, categoria="", pais="DE", ip="203.0.113.5"),
            # 3) ja verificado pela Cloudflare (categoria preenchida), IP
            #    dentro da faixa -> NAO conta de novo (ja esta no lote primario)
            _grupo(5, PERPLEXITYBOT_UA, categoria="search_engine_crawler", ip="18.97.9.99"),
            # 4) BR de operador sempre-estrangeiro -> ja virou local_verification
            #    no lote primario, NAO pode ser "movido" aqui
            _grupo(7, PERPLEXITYBOT_UA, categoria="", pais="BR", ip="18.97.9.98"),
            # 5) UA de OUTRO agente (Perplexity-User) que o filtro OR largo
            #    também trouxe -> descartado, nao pertence a perplexitybot
            _grupo(999, PERPLEXITY_USER_UA, categoria="", ip="18.97.9.97"),
        ]
        amostrado, estimado, paises = gbad._processar_grupos_secundarios(
            grupos, "perplexitybot", FAIXA_PERPLEXITYBOT)

        self.assertEqual(amostrado, 500)  # so os dois grupos (1)
        self.assertEqual(estimado, 500.0)
        self.assertEqual(paises, {"US": 500})


class TestAplicaFase2IPRange(unittest.TestCase):
    def test_clamp_nunca_ultrapassa_o_unverified_original(self):
        dados = {
            "requests_sampled_unverified_ua": 532,
            "requests_estimated_unverified_ua": 532.0,
            "countries": {},
            "countries_unverified": {"US": 500, "DE": 32},
        }
        gbad._aplicar_fase2_ip_range(dados, movido_amostrado=500, movido_estimado=500.0,
                                      paises_movidos={"US": 500})

        self.assertEqual(dados["requests_sampled_ip_range"], 500)
        self.assertEqual(dados["requests_sampled_unverified_ua"], 32)
        self.assertEqual(dados["countries_unverified"], {"DE": 32})
        # O que saiu de "sem verificacao" tem que reaparecer em `countries` —
        # o mesmo campo que ja recebe a perna Cloudflare. Sem isto, trafego
        # verificado por faixa de IP ficava sem pais em lugar nenhum.
        self.assertEqual(dados["countries"], {"US": 500})

    def test_movido_maior_que_disponivel_e_reduzido_ao_disponivel(self):
        # Drift entre as duas consultas (a janela de "hoje" segue acumulando):
        # o movido nao pode superar o que a primaria contou como unverified.
        dados = {
            "requests_sampled_unverified_ua": 10,
            "requests_estimated_unverified_ua": 10.0,
            "countries": {},
            "countries_unverified": {"US": 10},
        }
        gbad._aplicar_fase2_ip_range(dados, movido_amostrado=999, movido_estimado=999.0,
                                      paises_movidos={"US": 999})

        self.assertEqual(dados["requests_sampled_ip_range"], 10)
        self.assertEqual(dados["requests_sampled_unverified_ua"], 0)


class TestAutenticidadeDe(unittest.TestCase):
    def test_tabela_das_quatro_combinacoes(self):
        self.assertEqual(gbad._autenticidade_de(0, 0), gbad.AUTENTICIDADE_NENHUMA)
        self.assertEqual(gbad._autenticidade_de(26, 0), gbad.AUTENTICIDADE_CLOUDFLARE)
        self.assertEqual(gbad._autenticidade_de(0, 500), gbad.AUTENTICIDADE_IP_RANGE)
        self.assertEqual(gbad._autenticidade_de(26, 500), gbad.AUTENTICIDADE_AMBAS)


class TestMontarRegistro(unittest.TestCase):
    def test_coerencia_e_metadados_de_faixa(self):
        dados = {
            "requests_sampled": 0,
            "requests_estimated": 0.0,
            "requests_local_verification": 0,
            "requests_sampled_unverified_ua": 32,
            "requests_estimated_unverified_ua": 32.0,
            "requests_sampled_ip_range": 500,
            "requests_estimated_ip_range": 500.0,
            "countries": {},
            "countries_unverified": {"DE": 32},
            "verified_bot_categories": {},
            "user_agents": {PERPLEXITYBOT_UA},
            "user_agents_unverified": {PERPLEXITYBOT_UA},
        }
        operadores = {"perplexitybot": ("perplexitybot", 8)}
        registro = gbad._montar_registro("2026-09-02", "perplexitybot", dados, operadores,
                                          "2026-09-02T00:00:00Z", "2026-09-02T23:59:59Z", False)

        self.assertEqual(registro["schema_version"], "edge_bot_agents_daily_v4")
        self.assertEqual(registro["requests_sampled"], 500)
        self.assertEqual(registro["requests_sampled_cloudflare_verified"], 0)
        self.assertEqual(registro["requests_sampled_ip_range"], 500)
        self.assertEqual(registro["authenticity"], "ip_range_at_edge")
        self.assertEqual(registro["ip_range_operator"], "perplexitybot")
        self.assertEqual(registro["ip_range_prefixes_total"], 8)
        # Coerencia exigida pelo contrato: sampled == cloudflare + ip_range.
        self.assertEqual(registro["requests_sampled"],
                          registro["requests_sampled_cloudflare_verified"]
                          + registro["requests_sampled_ip_range"])

    def test_sem_operador_conhecido_fica_none_nao_zero_disfarcado(self):
        dados = {
            "requests_sampled": 50, "requests_estimated": 50.0,
            "requests_local_verification": 0,
            "requests_sampled_unverified_ua": 0, "requests_estimated_unverified_ua": 0.0,
            "countries": {"US": 50}, "countries_unverified": {},
            "verified_bot_categories": {"search_engine_crawler": 50},
            "user_agents": {YANDEXBOT_UA}, "user_agents_unverified": set(),
        }
        registro = gbad._montar_registro("2026-09-02", "yandexbot", dados, operadores={},
                                          ini_str="2026-09-02T00:00:00Z",
                                          fim_str="2026-09-02T23:59:59Z", truncado=False)
        self.assertIsNone(registro["ip_range_operator"])
        self.assertEqual(registro["ip_range_prefixes_total"], 0)
        self.assertEqual(registro["authenticity"], "cloudflare_verified_bot_category")


class TestParticaoQuatroCenarios(unittest.TestCase):
    """Os quatro cenários pedidos: Perplexity em faixa, Perplexity fora de
    faixa, Googlebot verificado pela CF, UA sem faixa — ponta a ponta, sem
    rede, exercitando exatamente as funções que `coletar_dia` orquestra."""

    def test_ponta_a_ponta(self):
        primaria = [
            # Googlebot: 100% verificado pela Cloudflare, zero unverified —
            # nunca vira candidato a segunda consulta.
            _grupo(26, GOOGLEBOT_UA, categoria="search_engine_crawler", pais="US"),
            # PerplexityBot: 532 sem verificacao nenhuma (a Cloudflare nao
            # verifica a Perplexity — medido em 2026-09-02). A consulta
            # primaria nao tem clientIP, entao tudo cai num unico total.
            _grupo(532, PERPLEXITYBOT_UA, categoria="", pais="US"),
            # YandexBot: sem verificacao, e SEM faixa oficial publicada —
            # fica sem verificacao dos dois jeitos.
            _grupo(12, YANDEXBOT_UA, categoria="", pais="RU"),
        ]
        por_agente = gbad._acumular_primario(primaria)
        faixas = {"perplexitybot": FAIXA_PERPLEXITYBOT}  # yandexbot fica de fora, de proposito
        operadores = {"perplexitybot": ("perplexitybot", 8)}

        candidatos = gbad._candidatos_ip_range(por_agente, faixas)
        self.assertEqual(candidatos, ["perplexitybot"])  # googlebot e yandexbot fora

        # Segunda consulta, so para perplexitybot: 500 dentro da faixa oficial
        # (Perplexity em faixa), 32 fora dela (Perplexity fora de faixa).
        secundaria = [
            _grupo(300, PERPLEXITYBOT_UA, categoria="", ip="18.97.9.100"),
            _grupo(200, PERPLEXITYBOT_UA, categoria="", ip="18.97.9.101"),
            _grupo(32, PERPLEXITYBOT_UA, categoria="", pais="DE", ip="203.0.113.5"),
        ]
        movido_amostrado, movido_estimado, paises_movidos = gbad._processar_grupos_secundarios(
            secundaria, "perplexitybot", faixas["perplexitybot"])
        gbad._aplicar_fase2_ip_range(por_agente["perplexitybot"], movido_amostrado,
                                      movido_estimado, paises_movidos)

        registros = {
            chave: gbad._montar_registro("2026-09-02", chave, dados, operadores,
                                          "2026-09-02T00:00:00Z", "2026-09-02T23:59:59Z", False)
            for chave, dados in por_agente.items()
        }

        # Cenario 1: Perplexity em faixa -> entrou em requests_sampled_ip_range.
        pplx = registros["perplexitybot"]
        self.assertEqual(pplx["requests_sampled_ip_range"], 500)
        self.assertEqual(pplx["requests_sampled"], 500)
        self.assertEqual(pplx["authenticity"], "ip_range_at_edge")
        self.assertEqual(pplx["ip_range_operator"], "perplexitybot")
        # A geografia do tráfego verificado por faixa de IP tem que aparecer
        # em `countries` — o mesmo campo que a perna Cloudflare usa.
        self.assertEqual(pplx["countries"], {"US": 500})

        # Cenario 2: Perplexity fora de faixa -> os 32 continuam nomeados,
        # nunca descartados em silencio.
        self.assertEqual(pplx["requests_sampled_unverified_ua"], 32)

        # Cenario 3: Googlebot verificado pela Cloudflare -> intocado pela fase 2.
        goog = registros["googlebot"]
        self.assertEqual(goog["requests_sampled"], 26)
        self.assertEqual(goog["requests_sampled_ip_range"], 0)
        self.assertEqual(goog["authenticity"], "cloudflare_verified_bot_category")

        # Cenario 4: UA sem faixa oficial -> continua sem verificacao nenhuma,
        # nunca reclassificado por adivinhacao.
        yandex = registros["yandexbot"]
        self.assertEqual(yandex["requests_sampled"], 0)
        self.assertEqual(yandex["requests_sampled_unverified_ua"], 12)
        self.assertEqual(yandex["authenticity"], "unverifiable_at_edge")
        self.assertIsNone(yandex["ip_range_operator"])

        # A soma de cada linha fecha exatamente entre as duas pernas — o
        # contrato de coerencia que edgetelemetry.avaliar_linha exige.
        for registro in registros.values():
            self.assertEqual(registro["requests_sampled"],
                              registro["requests_sampled_cloudflare_verified"]
                              + registro["requests_sampled_ip_range"])


if __name__ == "__main__":
    unittest.main()
