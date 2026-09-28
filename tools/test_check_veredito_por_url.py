#!/usr/bin/env python3
"""Testes de tools/check-veredito-por-url.

O que estes testes exercitam é o CORTE, não a rede nem o disco de produção:
`analisar_linha` e `classificar` são funções puras, então as fixtures fabricam
linhas de log sintéticas e um mapa de borda sintético. Os dois testes de
integração montam um repositório inteiro em diretório temporário — nenhum toca
`/var/log/nginx` nem `data/ops/`.

Cada FALSO POSITIVO abaixo tem de REPROVAR o comportamento errado, não só passar
no certo: por isso cada um afirma o motivo do descarte E afirma que a rota
continua fora da contagem de rastreio. Um teste que só verificasse "classificou
alguma coisa" passaria com o detector quebrado.

Casos:
  1. URL no sitemap sem requisição                    -> NUNCA_PEDIDA
  2. URL com 1 requisição                             -> PEDIDA_UMA_VEZ_SO
  3. URL com 2 requisições em datas distintas         -> PEDIDA_E_REVISITADA
  4. FP1: duas requisições no MESMO dia               -> NÃO é revisita
  5. FP2: UA Googlebot com IP fora das faixas         -> descartada (forjada).
          É o defeito que já inflou uma série deste repositório em 258x.
  6. FP3: `warm=` diferente de `-` (aquecimento)      -> descartada
  7. FP4: rota fora do sitemap                        -> fora do denominador
  8. FP5: `bot_sim=true` vindo de IP DENTRO da faixa  -> descartada. Medido em
          access.log.16.gz: 1.200 linhas assim, de 66.249.66.1, que é faixa
          oficial do Google — a verificação de IP sozinha aceitaria todas.
  9. FP6: Chrome-Lighthouse (UA tem `Googlebot/2.1`,  -> descartada
          IP é 66.249.*)
 10. rotação antiga, sem o campo `warm=`              -> ACEITA (ausente não é
          aquecimento; o log_format ganhou o campo depois)
 11. borda + origem em datas distintas                -> PEDIDA_E_REVISITADA
 12. invariante: os três estados somam o denominador
 13. integração: estado da borda ausente              -> exit 2 (inconclusivo)
 14. integração: --registrar grava UMA linha na série
 15. integração: glob de log sem arquivo nenhum -> ainda ha veredito pela
     borda, marcado como piso (o caminho PermissionError -> sudo nao tem
     teste: depende do ambiente, e um chmod 000 num teste mediria o
     sistema de arquivos, nao o instrumento)
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import ipaddress
import json
import os
import tempfile
import unittest

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.path.join(TOOLS_DIR, "check-veredito-por-url")


def _load_module():
    loader = importlib.machinery.SourceFileLoader(
        "check_veredito_por_url_under_test", SCRIPT_PATH)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


MOD = _load_module()

UA_GOOGLEBOT = ("Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.175 "
                "Mobile Safari/537.36 (compatible; Googlebot/2.1; "
                "+http://www.google.com/bot.html)")
# UA REAL do PageSpeed Insights: carrega `Googlebot/2.1` e roda de 66.249.*.
UA_LIGHTHOUSE = UA_GOOGLEBOT + " Chrome-Lighthouse"
UA_VISITANTE = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# 66.249.64.0/19 é bloco publicado pelo Google; 45.33.32.0/24 é público e NÃO é
# do Google — serve de "forjador" com IP roteável, para o FP2 medir a faixa e
# não cair no descarte mais fácil de endereço privado.
REDES_PRIMARIAS = [ipaddress.ip_network("66.249.64.0/19"),
                   ipaddress.ip_network("2001:4860:4801:10::/64")]
REDES_SECUNDARIAS = [ipaddress.ip_network("74.125.0.0/16")]
HOSTS = {"wikijuridica.com.br", "www.wikijuridica.com.br"}

IP_GOOGLE = "66.249.73.98"
IP_GOOGLE_2 = "66.249.66.1"
IP_FORJADOR = "45.33.32.156"

SITEMAP = {
    "/familia/divorcio-consensual/",
    "/previdenciario/auxilio-doenca-negado/",
    "/trabalhista/rescisao-indireta/",
    "/glossario/usucapiao/",
}


def linha_log(ip=IP_GOOGLE, quando="12/Aug/2026:03:04:48", rota="/familia/divorcio-consensual/",
              ua=UA_GOOGLEBOT, bot_sim="-", warm="-", host="wikijuridica.com.br",
              status="200", com_warm=True, com_bot_sim=True):
    """Uma linha no formato wj_main, com os campos opcionais controláveis."""
    cauda = "allow=1"
    if com_bot_sim:
        cauda += " bot_sim=%s" % bot_sim
    cauda += " rt=0.000 cf_ray=a321a58e1ca1f05f-GIG reqlen=566 ref=\"-\""
    if com_warm:
        cauda += " warm=%s inm=- ims=-" % warm
    return ('%s - [%s -0300] host=%s "GET %s HTTP/1.1" %s 27020 "%s" %s'
            % (ip, quando, host, rota, status, ua, cauda))


def aceitar(bruto):
    return MOD.analisar_linha(bruto, REDES_PRIMARIAS, REDES_SECUNDARIAS, HOSTS)


def classificar(linhas, borda=None):
    aceitas = []
    for bruto in linhas:
        veredito = aceitar(bruto)
        if veredito["aceita"]:
            aceitas.append(veredito)
    return MOD.classificar(SITEMAP, aceitas, borda or {}), aceitas


class EstadosTest(unittest.TestCase):
    def test_1_sem_requisicao_e_nunca_pedida(self):
        resultado, _ = classificar([])
        self.assertEqual(resultado["contagem"][MOD.ESTADO_NUNCA], len(SITEMAP))
        self.assertEqual(
            resultado["por_rota"]["/familia/divorcio-consensual/"]["estado"],
            MOD.ESTADO_NUNCA)

    def test_2_uma_requisicao_e_pedida_uma_vez_so(self):
        resultado, aceitas = classificar([linha_log()])
        self.assertEqual(len(aceitas), 1)
        rota = resultado["por_rota"]["/familia/divorcio-consensual/"]
        self.assertEqual(rota["estado"], MOD.ESTADO_UMA_VEZ)
        self.assertEqual(rota["datas_log"], ["2026-08-12"])
        self.assertEqual(resultado["contagem"][MOD.ESTADO_NUNCA], len(SITEMAP) - 1)

    def test_3_duas_datas_distintas_e_revisitada(self):
        resultado, _ = classificar([
            linha_log(quando="12/Aug/2026:03:04:48"),
            linha_log(quando="26/Aug/2026:11:20:01"),
        ])
        rota = resultado["por_rota"]["/familia/divorcio-consensual/"]
        self.assertEqual(rota["estado"], MOD.ESTADO_REVISITADA)
        self.assertEqual(rota["datas_distintas"], 2)


class FalsosPositivosTest(unittest.TestCase):
    def test_4_fp1_duas_no_mesmo_dia_nao_sao_revisita(self):
        resultado, aceitas = classificar([
            linha_log(quando="12/Aug/2026:03:04:48"),
            linha_log(quando="12/Aug/2026:19:57:02"),
        ])
        # As DUAS linhas são legítimas e foram aceitas...
        self.assertEqual(len(aceitas), 2)
        rota = resultado["por_rota"]["/familia/divorcio-consensual/"]
        # ...e mesmo assim não houve revisita: voltar é em OUTRO dia.
        self.assertNotEqual(rota["estado"], MOD.ESTADO_REVISITADA)
        self.assertEqual(rota["estado"], MOD.ESTADO_UMA_VEZ)
        self.assertEqual(rota["datas_distintas"], 1)
        self.assertEqual(resultado["contagem"][MOD.ESTADO_REVISITADA], 0)

    def test_5_fp2_ua_googlebot_com_ip_fora_das_faixas_nao_conta(self):
        veredito = aceitar(linha_log(ip=IP_FORJADOR))
        self.assertFalse(veredito["aceita"])
        self.assertEqual(veredito["motivo"], "ip_fora_das_faixas")
        # E o efeito no veredito: a rota continua NUNCA_PEDIDA, não vira
        # "rastreada". Contar por string de UA deu 3.535 onde o IP dá 20.
        resultado, aceitas = classificar([linha_log(ip=IP_FORJADOR)])
        self.assertEqual(aceitas, [])
        self.assertEqual(
            resultado["por_rota"]["/familia/divorcio-consensual/"]["estado"],
            MOD.ESTADO_NUNCA)
        self.assertEqual(resultado["contagem"][MOD.ESTADO_NUNCA], len(SITEMAP))

    def test_5b_ip_privado_ou_de_documentacao_tambem_nao_conta(self):
        for ip in ("127.0.0.1", "203.0.113.7", "10.1.2.3"):
            veredito = aceitar(linha_log(ip=ip))
            self.assertFalse(veredito["aceita"], ip)
            self.assertEqual(veredito["motivo"], "ip_nao_publico", ip)

    def test_6_fp3_aquecimento_proprio_nao_conta(self):
        veredito = aceitar(linha_log(warm="true"))
        self.assertFalse(veredito["aceita"])
        self.assertEqual(veredito["motivo"], "aquecimento_proprio")
        resultado, aceitas = classificar([linha_log(warm="true")])
        self.assertEqual(aceitas, [])
        self.assertEqual(
            resultado["por_rota"]["/familia/divorcio-consensual/"]["estado"],
            MOD.ESTADO_NUNCA)

    def test_7_fp4_rota_fora_do_sitemap_nao_entra_no_denominador(self):
        resultado, aceitas = classificar([
            linha_log(rota="/robots.txt"),
            linha_log(rota="/sitemaps/pages-0027.xml"),
            linha_log(rota="/rota-que-nao-existe-no-sitemap/"),
        ])
        # As três são requisições verificadas de verdade...
        self.assertEqual(len(aceitas), 3)
        # ...e nenhuma muda o denominador nem cria rota nova no veredito.
        self.assertEqual(len(resultado["por_rota"]), len(SITEMAP))
        self.assertEqual(resultado["requisicoes_fora_do_sitemap"], 3)
        self.assertEqual(resultado["contagem"][MOD.ESTADO_NUNCA], len(SITEMAP))
        self.assertNotIn("/robots.txt", resultado["por_rota"])

    def test_8_fp5_bot_sim_de_ip_oficial_nao_conta(self):
        # O caso medido: 1.200 linhas `bot_sim=true` saindo de 66.249.66.1, que
        # ESTÁ na faixa oficial. Sem este descarte, a sonda desta casa entraria
        # na métrica — fraude, não medição.
        bruto = linha_log(ip=IP_GOOGLE_2, bot_sim="true")
        self.assertTrue(MOD.botagents.em_faixa(IP_GOOGLE_2, REDES_PRIMARIAS),
                        "a fixture precisa de um IP DENTRO da faixa para o teste valer")
        veredito = aceitar(bruto)
        self.assertFalse(veredito["aceita"])
        self.assertEqual(veredito["motivo"], "simulacao_propria")
        resultado, _ = classificar([bruto])
        self.assertEqual(resultado["contagem"][MOD.ESTADO_NUNCA], len(SITEMAP))

    def test_9_fp6_chrome_lighthouse_nao_e_googlebot(self):
        bruto = linha_log(ua=UA_LIGHTHOUSE)
        self.assertIn("googlebot/2.1", UA_LIGHTHOUSE.lower(),
                      "o UA do Lighthouse tem de conter a marca, senao o teste nao mede nada")
        veredito = aceitar(bruto)
        self.assertFalse(veredito["aceita"])
        self.assertEqual(veredito["motivo"], "ua_de_outro_agente")

    def test_9b_visitante_humano_nao_conta(self):
        veredito = aceitar(linha_log(ua=UA_VISITANTE))
        self.assertFalse(veredito["aceita"])
        self.assertEqual(veredito["motivo"], "ua_nao_googlebot")

    def test_9c_host_de_outro_site_nao_conta(self):
        veredito = aceitar(linha_log(host="outro-portal.example"))
        self.assertFalse(veredito["aceita"])
        self.assertEqual(veredito["motivo"], "host_de_outro_site")

    def test_9d_host_www_conta(self):
        veredito = aceitar(linha_log(host="www.wikijuridica.com.br"))
        self.assertTrue(veredito["aceita"])


class FormatoAntigoTest(unittest.TestCase):
    def test_10_rotacao_sem_campo_warm_e_aceita(self):
        # access.log.16.gz (11-12/08) não tem `warm=`: o log_format ganhou o
        # campo depois. Exigi-lo descartaria em silêncio a janela do pico de
        # rastreio que esta frente investiga.
        bruto = linha_log(com_warm=False)
        self.assertNotIn("warm=", bruto)
        veredito = aceitar(bruto)
        self.assertTrue(veredito["aceita"], veredito.get("motivo"))
        self.assertEqual(veredito["data"], "2026-08-12")

    def test_10b_rotacao_sem_bot_sim_e_sem_warm_e_aceita(self):
        bruto = linha_log(com_warm=False, com_bot_sim=False)
        veredito = aceitar(bruto)
        self.assertTrue(veredito["aceita"], veredito.get("motivo"))

    def test_10c_query_string_nao_cria_rota_nova(self):
        veredito = aceitar(linha_log(rota="/familia/divorcio-consensual/?utm_source=x"))
        self.assertTrue(veredito["aceita"])
        self.assertEqual(veredito["rota"], "/familia/divorcio-consensual/")

    def test_10d_status_nao_filtra_o_toque_do_bot(self):
        for status in ("200", "301", "304", "404"):
            veredito = aceitar(linha_log(status=status))
            self.assertTrue(veredito["aceita"], status)


class FusaoComABordaTest(unittest.TestCase):
    def test_11_borda_e_origem_em_datas_distintas_e_revisita(self):
        borda = {"/familia/divorcio-consensual/": "2026-08-08"}
        resultado, _ = classificar([linha_log(quando="26/Aug/2026:11:20:01")], borda)
        rota = resultado["por_rota"]["/familia/divorcio-consensual/"]
        self.assertEqual(rota["estado"], MOD.ESTADO_REVISITADA)
        self.assertEqual(rota["fonte"], "log+borda")

    def test_11b_borda_e_origem_no_mesmo_dia_nao_e_revisita(self):
        # A borda VÊ a requisição que a origem viu (a origem é subconjunto).
        # Somar as duas como se fossem eventos diferentes inventaria revisita.
        borda = {"/familia/divorcio-consensual/": "2026-08-12"}
        resultado, _ = classificar([linha_log(quando="12/Aug/2026:03:04:48")], borda)
        rota = resultado["por_rota"]["/familia/divorcio-consensual/"]
        self.assertEqual(rota["estado"], MOD.ESTADO_UMA_VEZ)

    def test_11c_rota_so_na_borda_nao_e_nunca_pedida(self):
        # O log da origem NÃO vê o que a borda serve de cache. Sem esta fusão,
        # a rota seria declarada NUNCA_PEDIDA — a mentira que o instrumento
        # existe para não contar.
        borda = {"/glossario/usucapiao/": "2026-08-10"}
        resultado, _ = classificar([], borda)
        self.assertEqual(resultado["por_rota"]["/glossario/usucapiao/"]["estado"],
                         MOD.ESTADO_UMA_VEZ)
        self.assertEqual(resultado["por_rota"]["/glossario/usucapiao/"]["fonte"], "borda")
        self.assertEqual(resultado["contagem"][MOD.ESTADO_NUNCA], len(SITEMAP) - 1)

    def test_11d_rota_da_borda_fora_do_sitemap_nao_entra(self):
        borda = {"/rota-aposentada/": "2026-08-10"}
        resultado, _ = classificar([], borda)
        self.assertEqual(len(resultado["por_rota"]), len(SITEMAP))
        self.assertNotIn("/rota-aposentada/", resultado["por_rota"])

    def test_11e_rota_so_no_log_e_contada_como_piso_da_borda(self):
        resultado, _ = classificar([linha_log()], {})
        self.assertEqual(resultado["rotas_so_no_log"], 1)


class InvarianteTest(unittest.TestCase):
    def test_12_os_tres_estados_somam_o_denominador(self):
        borda = {"/glossario/usucapiao/": "2026-08-10",
                 "/trabalhista/rescisao-indireta/": "2026-08-11"}
        linhas = [
            linha_log(quando="12/Aug/2026:03:04:48"),
            linha_log(quando="26/Aug/2026:11:20:01"),
            linha_log(rota="/trabalhista/rescisao-indireta/", quando="20/Aug/2026:01:00:00"),
            linha_log(rota="/robots.txt"),
            linha_log(ip=IP_FORJADOR, rota="/previdenciario/auxilio-doenca-negado/"),
        ]
        resultado, _ = classificar(linhas, borda)
        registro = MOD.montar_registro(len(SITEMAP), resultado, {"gerado_em": "2026-08-28T00:00:00Z"})
        self.assertTrue(registro["soma_confere"])
        self.assertEqual(registro["soma_dos_estados"], len(SITEMAP))
        self.assertEqual(registro["nunca_pedida"], 1)          # auxilio-doenca (forjada)
        self.assertEqual(registro["pedida_uma_vez_so"], 1)     # usucapiao (só borda)
        self.assertEqual(registro["pedida_e_revisitada"], 2)   # divorcio e rescisao
        # Os dois eixos, separados: 3 achadas de 4, 2 delas com revisita.
        self.assertEqual(registro["descobertas"], 3)
        self.assertEqual(registro["descobertas"] + registro["nunca_pedida"],
                         registro["denominador"])
        self.assertTrue(registro["cobertura_e_piso"])
        self.assertEqual(registro["schema_version"], MOD.SCHEMA)


def _montar_repo(tmp, com_borda=True):
    os.makedirs(os.path.join(tmp, "public", "sitemaps"))
    os.makedirs(os.path.join(tmp, "data", "ops", "bot_ip_ranges"))
    with open(os.path.join(tmp, "public", "sitemaps", "pages-0001.xml"), "w",
              encoding="utf-8") as handle:
        handle.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset>\n')
        for rota in sorted(SITEMAP):
            handle.write("<url><loc>https://wikijuridica.com.br%s</loc></url>\n" % rota)
        handle.write("</urlset>\n")
    with open(os.path.join(tmp, "data", "ops", "bot_ip_ranges", "googlebot.json"), "w",
              encoding="utf-8") as handle:
        json.dump({"authenticates_agents": ["googlebot"],
                   "prefixes": ["66.249.64.0/19"]}, handle)
    if com_borda:
        with open(os.path.join(tmp, "data", "ops", "crawl_coverage_state.json"), "w",
                  encoding="utf-8") as handle:
            json.dump({"crawlers_verified": {"googlebot": {
                "paths_first_seen": {"/glossario/usucapiao/": "2026-08-10"},
                "days_ingested": ["2026-08-10", "2026-08-11"],
                "last_updated": "2026-08-28T04:12:14Z"}}}, handle)
    caminho_log = os.path.join(tmp, "access.log")
    with open(caminho_log, "w", encoding="utf-8") as handle:
        handle.write(linha_log(quando="12/Aug/2026:03:04:48") + "\n")
        handle.write(linha_log(quando="26/Aug/2026:11:20:01") + "\n")
        handle.write(linha_log(ip=IP_FORJADOR, rota="/trabalhista/rescisao-indireta/") + "\n")
        handle.write(linha_log(ua=UA_VISITANTE, rota="/glossario/usucapiao/") + "\n")
    return caminho_log


class IntegracaoTest(unittest.TestCase):
    def test_13_borda_ausente_e_inconclusivo_nao_reprovacao(self):
        with tempfile.TemporaryDirectory() as tmp:
            caminho_log = _montar_repo(tmp, com_borda=False)
            codigo = MOD.main(["--root", tmp, "--log-glob", caminho_log, "--json"])
            # 2, nunca 1: sem a camada da borda o veredito NUNCA_PEDIDA seria
            # mentira, e indisponibilidade de fonte não é reprovação.
            self.assertEqual(codigo, 2)

    def test_14_registrar_grava_uma_linha_coerente(self):
        with tempfile.TemporaryDirectory() as tmp:
            caminho_log = _montar_repo(tmp)
            codigo = MOD.main(["--root", tmp, "--log-glob", caminho_log, "--registrar"])
            self.assertEqual(codigo, 0)
            serie = os.path.join(tmp, MOD.SERIE)
            with open(serie, encoding="utf-8") as handle:
                linhas = handle.read().strip().splitlines()
            self.assertEqual(len(linhas), 1)
            registro = json.loads(linhas[0])
            self.assertEqual(registro["denominador"], len(SITEMAP))
            self.assertTrue(registro["soma_confere"])
            self.assertEqual(registro["pedida_e_revisitada"], 1)   # divorcio, 2 datas
            self.assertEqual(registro["pedida_uma_vez_so"], 1)     # usucapiao, só borda
            self.assertEqual(registro["nunca_pedida"], 2)          # rescisao (forjada) e auxilio
            self.assertEqual(registro["requisicoes_aceitas"], 2)
            self.assertEqual(registro["descartes_por_motivo"].get("ip_fora_das_faixas"), 1)
            self.assertEqual(registro["janela_log_inicio"], "2026-08-12T03:04:48")
            self.assertEqual(registro["janela_log_fim"], "2026-08-26T11:20:01")
            self.assertEqual(registro["janela_borda_inicio"], "2026-08-10")
            self.assertTrue(registro["cobertura_e_piso"])
            # Segunda execução acrescenta, nunca reescreve.
            MOD.main(["--root", tmp, "--log-glob", caminho_log, "--registrar"])
            with open(serie, encoding="utf-8") as handle:
                self.assertEqual(len(handle.read().strip().splitlines()), 2)

    def test_15_glob_sem_arquivo_nao_vira_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            _montar_repo(tmp)
            ausente = os.path.join(tmp, "nao-existe.log")
            codigo = MOD.main(["--root", tmp, "--log-glob", ausente, "--json"])
            # Glob sem nenhum arquivo: não há rotação para declarar inacessível,
            # mas a borda ainda responde — o veredito sai, marcado como piso.
            self.assertEqual(codigo, 0)


# --------------------------------------------------------------------------
# Os testes acima provam que o instrumento acerta. Este prova que eles PEGAM o
# erro — que é outra coisa.
#
# Um teste que só afirma o comportamento certo continua passando com a guarda
# apagada, se o caminho certo não depender dela. Aqui cada guarda é REMOVIDA
# numa cópia temporária do script e a suíte roda contra o mutante: se o teste
# correspondente não reprovar, a guarda não estava sendo medida por ninguém e
# esta classe falha dizendo qual.
#
# `VEREDITO_MUTACAO` corta a recursão: o mutante roda esta mesma suíte, e sem a
# variável ele tentaria mutar a si mesmo, sem fim.
# --------------------------------------------------------------------------

MUTACOES = (
    ("guarda de bot_sim (simulacao desta casa com UA e IP do Google)",
     '    if (casou.group("sim") or "-") not in ("-", ""):\n'
     '        return {"aceita": False, "motivo": "simulacao_propria"}\n',
     "",
     "FalsosPositivosTest.test_8_fp5_bot_sim_de_ip_oficial_nao_conta"),
    ("guarda de warm (aquecimento proprio)",
     '    if (casou.group("warm") or "-") not in ("-", ""):\n'
     '        return {"aceita": False, "motivo": "aquecimento_proprio"}\n',
     "",
     "FalsosPositivosTest.test_6_fp3_aquecimento_proprio_nao_conta"),
    ("verificacao de faixa oficial de IP",
     '    else:\n        return {"aceita": False, "motivo": "ip_fora_das_faixas"}',
     '    else:\n        faixa = "sem_verificacao"',
     "FalsosPositivosTest.test_5_fp2_ua_googlebot_com_ip_fora_das_faixas_nao_conta"),
    ("revisita por DATA distinta (mutante conta requisicao)",
     '        datas_log[rota].add(registro["data"])',
     '        datas_log[rota].add(registro["data"] + str(len(datas_log[rota])))',
     "FalsosPositivosTest.test_4_fp1_duas_no_mesmo_dia_nao_sao_revisita"),
    ("separacao Chrome-Lighthouse x Googlebot",
     '    if botagents.agente_de(ua) != AGENTE_ALVO:\n'
     '        return {"aceita": False, "motivo": "ua_de_outro_agente"}\n',
     "",
     "FalsosPositivosTest.test_9_fp6_chrome_lighthouse_nao_e_googlebot"),
    ("denominador fechado no sitemap",
     "        if rota not in rotas_sitemap:",
     "        if False:",
     "FalsosPositivosTest.test_7_fp4_rota_fora_do_sitemap_nao_entra_no_denominador"),
)


@unittest.skipIf(os.environ.get("VEREDITO_MUTACAO"), "execucao mutante: nao recursar")
class GuardaSaoMedidasTest(unittest.TestCase):
    def test_cada_guarda_removida_reprova_o_teste_dela(self):
        import shutil
        import subprocess
        import sys

        with open(SCRIPT_PATH, encoding="utf-8") as handle:
            original = handle.read()
        ambiente = dict(os.environ, VEREDITO_MUTACAO="1")
        nao_detectados = []
        for nome, agulha, troca, teste in MUTACOES:
            self.assertIn(agulha, original,
                          "ancora da mutacao '%s' sumiu do script: a guarda mudou de "
                          "forma e precisa ser re-verificada, nao apagada daqui" % nome)
            with tempfile.TemporaryDirectory() as tmp:
                destino = os.path.join(tmp, os.path.basename(SCRIPT_PATH))
                shutil.copy(os.path.join(TOOLS_DIR, "botagents.py"), tmp)
                copia_teste = os.path.join(tmp, os.path.basename(__file__))
                shutil.copy(os.path.abspath(__file__), copia_teste)

                def rodar():
                    return subprocess.run([sys.executable, copia_teste, teste],
                                          capture_output=True, text=True,
                                          env=ambiente, timeout=120)

                # CONTROLE, antes da mutação: o mesmo comando contra o script
                # ÍNTEGRO tem de PASSAR. Sem ele, um nome de teste digitado
                # errado sairia com código != 0 (unittest não acha o teste) e
                # esta classe leria isso como "a guarda foi medida" — falso
                # positivo dentro do próprio detector de falso positivo.
                with open(destino, "w", encoding="utf-8") as handle:
                    handle.write(original)
                controle = rodar()
                self.assertEqual(
                    controle.returncode, 0,
                    "controle falhou para %s — o teste nao passa nem com o script "
                    "integro, entao a reprovacao do mutante nao prova nada:\n%s"
                    % (teste, controle.stderr[-600:]))

                with open(destino, "w", encoding="utf-8") as handle:
                    handle.write(original.replace(agulha, troca, 1))
                saida = rodar()
            if saida.returncode == 0:
                nao_detectados.append("%s (esperado reprovar %s)" % (nome, teste))
        self.assertEqual(nao_detectados, [],
                         "guarda(s) que ninguem mede — o teste passa com a guarda "
                         "removida: %s" % nao_detectados)


if __name__ == "__main__":
    unittest.main(verbosity=2)
