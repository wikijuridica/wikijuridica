#!/usr/bin/env python3
"""Prova as decisões que fazem `generate-social-bot-coverage` medir em vez de opinar.

Cada teste aqui corresponde a uma forma de a série mentir a nosso favor, e todas
as cinco já aconteceram em séries deste projeto:

  1. classificar como FORJADO quem não tinha método de verificação (foi o defeito
     do `origin_bot_traffic_daily_v2`, corrigido no v3);
  2. classificar como FORJADO a linha cujo IP foi PSEUDONIMIZADO por dever de
     LGPD — transformar proteção de dado pessoal em acusação de fraude;
  3. omitir a linha `redesocial = 0`, deixando "nenhum bot pediu a rede social"
     indistinguível de "o coletor parou";
  4. emitir zeros para um dia inteiro que ninguém classificou por superfície
     (ledger `origin_access_nginx_v1`), fabricando medição;
  5. deixar `req_por_url` virar `0.0` ou `inf` quando o denominador não pôde ser
     medido, em vez de `null` com o motivo escrito.

E uma que ainda não aconteceu, e não pode acontecer: dado pessoal na série. O
ledger de origem carrega `remote_addr` e `user_agent`, e o caminho da rede social
carrega o termo que o visitante buscou. Nada disso pode atravessar para cá.
"""

import collections
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = SourceFileLoader("gerador_cobertura",
                     os.path.join(RAIZ, "tools/generate-social-bot-coverage")).load_module()

# Faixas SINTÉTICAS: os testes de classificação não dependem do bloco que a
# OpenAI publicou hoje.
#
# POR QUE NÃO SE USA A FAIXA DE DOCUMENTAÇÃO (RFC 5737, 203.0.113.0/24), que
# seria o certo num teste comum: `botagents.ip_nao_publico` a desconta —
# corretamente, porque quem vem de faixa não-roteável não é audiência —, e a
# linha inteira sumiria antes de chegar ao classificador. O mesmo vale para
# 198.18.0.0/15 (RFC 2544), que `ipaddress` também marca como privada. Então as
# fixtures usam endereços PÚBLICOS roteáveis, de infraestrutura pública e de
# nenhum visitante: 192.178.4.0/24 é bloco publicado pelo próprio Google em
# `data/ops/bot_ip_ranges/googlebot.json`, e 185.199.108.153 é CDN de hospedagem
# de projeto — nenhum dos dois é dado pessoal, e nenhum é de visitante medido.
FAIXAS = {"gptbot": [__import__("ipaddress").ip_network("192.178.4.0/24")]}
IP_NA_FAIXA = "192.178.4.1"
IP_FORA_DA_FAIXA = "185.199.108.153"

DENOMINADORES_OK = {
    "acervo": (10141, "data/editorial/published_manifest.jsonl", None),
    "redesocial": (35, "/redesocial/sitemap.xml", None),
}
DENOMINADORES_SEM_SOCIAL = {
    "acervo": (10141, "data/editorial/published_manifest.jsonl", None),
    "redesocial": (None, "/redesocial/sitemap.xml",
                   "processo_da_rede_social_fora_do_ar"),
}


def linha_do_ledger(**campos):
    """Uma linha de `origin_access_nginx_v2` com os defaults que não interessam
    ao caso, para que cada teste mostre só o que ele está variando."""
    registro = {
        "schema_version": "origin_access_nginx_v2",
        "origem": "nginx",
        "ts": "2026-09-05T10:00:00Z",
        "method": "GET",
        "path": "/familia/divorcio-consensual/",
        "status": 200,
        "bytes": 20000,
        "route_class": "page",
        "superficie": "acervo",
        "user_agent": "Mozilla/5.0 (compatible; GPTBot/1.2; +https://openai.com/gptbot)",
        "agent_key": "gptbot",
        "bot_allow": "1",
        "remote_addr": IP_NA_FAIXA,
        "remote_addr_forma": "ip",
        "warming": False,
        "bot_simulation": False,
    }
    registro.update(campos)
    return registro


def uma_linha_da_serie(registros, superficie="acervo", agente="gptbot", sem_rdns=True):
    agregado, contadores, metodos = G.agrega(registros, FAIXAS, sem_rdns=sem_rdns)
    linhas = G.monta_linhas("2026-09-05", agregado, metodos, contadores,
                            DENOMINADORES_OK, FAIXAS, sem_rdns, "2026-09-05T12:00:00Z")
    for linha in linhas:
        if linha["agent_key"] == agente and linha["superficie"] == superficie:
            return linha
    return None


class Classificacao(unittest.TestCase):
    def test_ip_na_faixa_oficial_e_autentico(self):
        linha = uma_linha_da_serie([linha_do_ledger()])
        self.assertEqual(linha["verification_method"], "ip_range")
        self.assertEqual(linha["requests_authentic"], 1)
        self.assertEqual(linha["requests_forged"], 0)
        self.assertEqual(linha["requests_unverifiable"], 0)

    def test_ip_fora_da_faixa_e_forjado_e_a_pista_livre_e_contada(self):
        """O número operacional: forjado que o mapa $wj_bot_allow isentou do
        rate limit por acreditar no User-Agent."""
        linha = uma_linha_da_serie([
            linha_do_ledger(remote_addr=IP_FORA_DA_FAIXA, bot_allow="1"),
            linha_do_ledger(remote_addr=IP_FORA_DA_FAIXA, bot_allow="0"),
        ])
        self.assertEqual(linha["requests_forged"], 2)
        self.assertEqual(linha["requests_forged_com_pista_livre"], 1)
        self.assertEqual(linha["requests_authentic"], 0)

    def test_agente_sem_metodo_e_nao_verificavel_nunca_forjado(self):
        """`semrushbot` não tem faixa publicada nem rDNS documentado. Não saber
        quem é não é o mesmo que saber que é falso — e `requests_forged > 0` com
        `verification_method: none` é a contradição que o gate de honestidade da
        série irmã reprova."""
        linha = uma_linha_da_serie(
            [linha_do_ledger(agent_key="semrushbot", remote_addr=IP_FORA_DA_FAIXA,
                             user_agent="Mozilla/5.0 (compatible; SemrushBot/7~bl)")],
            agente="semrushbot")
        self.assertEqual(linha["verification_method"], "none")
        self.assertEqual(linha["requests_unverifiable"], 1)
        self.assertEqual(linha["requests_forged"], 0)

    def test_ip_pseudonimizado_e_nao_verificavel_e_sai_nomeado(self):
        """A linha social vai para o git com HMAC no lugar do IP (LGPD art. 5º,
        II). Ela NÃO pode virar forjada: o pseudônimo não está fora da faixa, ele
        não é endereço nenhum."""
        linha = uma_linha_da_serie(
            [linha_do_ledger(superficie="redesocial", path="/redesocial/perguntas/",
                             remote_addr="pseud_" + "a" * 32,
                             remote_addr_forma="pseudonimo_diario")],
            superficie="redesocial")
        self.assertEqual(linha["requests"], 1)
        self.assertEqual(linha["requests_forged"], 0)
        self.assertEqual(linha["requests_unverifiable"], 1)
        self.assertEqual(linha["requests_pseudonimizadas_sem_veredito"], 1)

    def test_a_soma_fecha_em_toda_linha(self):
        """requests == authentic + forged + unverifiable. É a invariante que
        `tools/check-bot-telemetry-honesty` cobra da série irmã, e uma linha que
        não fecha esconde requisição que ninguém classificou."""
        registros = [
            linha_do_ledger(),
            linha_do_ledger(remote_addr=IP_FORA_DA_FAIXA),
            linha_do_ledger(agent_key="semrushbot",
                            user_agent="Mozilla/5.0 (compatible; SemrushBot/7~bl)"),
            linha_do_ledger(superficie="redesocial", path="/redesocial/",
                            remote_addr="pseud_" + "b" * 32,
                            remote_addr_forma="pseudonimo_diario"),
        ]
        agregado, contadores, metodos = G.agrega(registros, FAIXAS, sem_rdns=True)
        linhas = G.monta_linhas("2026-09-05", agregado, metodos, contadores,
                                DENOMINADORES_OK, FAIXAS, True, "2026-09-05T12:00:00Z")
        self.assertTrue(linhas)
        for linha in linhas:
            self.assertEqual(
                linha["requests"],
                linha["requests_authentic"] + linha["requests_forged"]
                + linha["requests_unverifiable"],
                "linha nao fecha: %r" % linha)


class ZeroEDado(unittest.TestCase):
    def test_agente_visto_so_no_acervo_ganha_linha_redesocial_zerada(self):
        """A linha `redesocial = 0` é o baseline contra o qual a canibalização se
        mede. Sem ela, "nenhum bot pediu a rede social" fica indistinguível de
        "o coletor parou"."""
        agregado, contadores, metodos = G.agrega([linha_do_ledger()], FAIXAS, sem_rdns=True)
        linhas = G.monta_linhas("2026-09-05", agregado, metodos, contadores,
                                DENOMINADORES_OK, FAIXAS, True, "2026-09-05T12:00:00Z")
        superficies = {linha["superficie"]: linha for linha in linhas}
        self.assertEqual(set(superficies), {"acervo", "redesocial"})
        self.assertEqual(superficies["redesocial"]["requests"], 0)
        self.assertEqual(superficies["redesocial"]["requests_authentic"], 0)
        # E o método continua sendo o do AGENTE, não "none" por não ter aparecido.
        self.assertEqual(superficies["redesocial"]["verification_method"], "ip_range")

    def test_dia_inteiro_em_v1_nao_gera_linha_nenhuma(self):
        """Antes de 2026-09-05 o ledger não tem `superficie`. Emitir zeros para
        um dia que ninguém classificou seria inventar medição."""
        with tempfile.TemporaryDirectory() as tmp:
            caminho = os.path.join(tmp, "nginx-2026-09-03.jsonl")
            with open(caminho, "w", encoding="utf-8") as handle:
                velha = linha_do_ledger()
                velha["schema_version"] = "origin_access_nginx_v1"
                velha.pop("superficie")
                velha.pop("remote_addr_forma")
                handle.write(json.dumps(velha) + "\n")
            registros, v1, ilegiveis = G.le_dia(tmp, "2026-09-03")
            self.assertEqual(registros, [])
            self.assertEqual(v1, 1)
            self.assertEqual(ilegiveis, 0)

    def test_superficie_interno_nao_entra_e_sai_contada(self):
        """`/healthz` não serve conteúdo a ninguém: somá-la ao acervo inflaria o
        denominador do lado que se quer proteger."""
        agregado, contadores, _metodos = G.agrega(
            [linha_do_ledger(superficie="interno", path="/healthz")], FAIXAS, sem_rdns=True)
        self.assertEqual(agregado, {})
        self.assertEqual(contadores["linhas_superficie_interno"], 1)


class JanelaPadrao(unittest.TestCase):
    """A série é APPEND. Se o padrão fosse "todos os dias que existirem", cada
    execução do timer reescreveria todo o histórico já gravado, e o arquivo
    cresceria com o quadrado do tempo — a mesma armadilha de inchaço que o
    ledger de borda deste projeto sofreu."""

    DIAS = ["2026-09-01", "2026-09-02", "2026-09-03", "2026-09-04", "2026-09-05"]

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        for dia in self.DIAS:
            caminho = os.path.join(self.tmp.name, "nginx-%s.jsonl" % dia)
            with open(caminho, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(linha_do_ledger()) + "\n")
        self.addCleanup(self.tmp.cleanup)

    def test_padrao_e_hoje_e_ontem(self):
        import datetime
        dias = G.janela_de_dias(self.tmp.name, hoje=datetime.date(2026, 9, 5))
        self.assertEqual(dias, ["2026-09-04", "2026-09-05"])

    def test_todos_faz_o_backfill(self):
        import datetime
        dias = G.janela_de_dias(self.tmp.name, todos=True, hoje=datetime.date(2026, 9, 5))
        self.assertEqual(dias, self.DIAS)

    def test_dia_explicito_vence_a_janela(self):
        import datetime
        dias = G.janela_de_dias(self.tmp.name, dia="2026-09-01",
                                hoje=datetime.date(2026, 9, 5))
        self.assertEqual(dias, ["2026-09-01"])

    def test_dia_da_janela_sem_ledger_nao_entra(self):
        """Pedir um dia que não tem arquivo produziria uma leitura vazia que o
        resumo confundiria com "nenhum bot naquele dia"."""
        import datetime
        dias = G.janela_de_dias(self.tmp.name, hoje=datetime.date(2026, 9, 20))
        self.assertEqual(dias, [])


class Denominador(unittest.TestCase):
    def test_sem_denominador_req_por_url_e_nulo_com_motivo(self):
        """Nunca 0.0 nem infinito: "não consegui medir" e "não há URL" são
        estados diferentes, e confundi-los manda apertar o parafuso errado."""
        agregado, contadores, metodos = G.agrega(
            [linha_do_ledger(superficie="redesocial", path="/redesocial/",
                             remote_addr=IP_NA_FAIXA)], FAIXAS, sem_rdns=True)
        linhas = G.monta_linhas("2026-09-05", agregado, metodos, contadores,
                                DENOMINADORES_SEM_SOCIAL, FAIXAS, True, "2026-09-05T12:00:00Z")
        social = [linha for linha in linhas if linha["superficie"] == "redesocial"][0]
        self.assertIsNone(social["urls_indexaveis"])
        self.assertIsNone(social["req_por_url"])
        self.assertEqual(social["motivo_do_denominador"], "processo_da_rede_social_fora_do_ar")

    def test_o_numerador_declarado_e_o_autentico(self):
        """Contar forjado no numerador faria o scanner que se passa por Googlebot
        elevar a cobertura do acervo."""
        linha = uma_linha_da_serie([
            linha_do_ledger(),
            linha_do_ledger(remote_addr=IP_FORA_DA_FAIXA),
        ])
        self.assertEqual(linha["req_por_url_numerador"], "requests_authentic")
        self.assertEqual(linha["requests"], 2)
        self.assertAlmostEqual(linha["req_por_url"], round(1 / 10141, 6))

    def test_acervo_conta_intent_distinto_e_so_o_indexavel(self):
        """Contar linha contaria a mesma URL duas vezes num dia de republicação;
        contar `noindex` inflaria o denominador com o que não é rastreável."""
        with tempfile.TemporaryDirectory() as tmp:
            caminho = os.path.join(tmp, "published_manifest.jsonl")
            with open(caminho, "w", encoding="utf-8") as handle:
                for registro in [
                    {"unique_intent_id": "a", "index_policy": "index"},
                    {"unique_intent_id": "a", "index_policy": "index"},
                    {"unique_intent_id": "b", "index_policy": "index"},
                    {"unique_intent_id": "c", "index_policy": "noindex"},
                ]:
                    handle.write(json.dumps(registro) + "\n")
            quantidade, fonte, motivo = G.urls_indexaveis_do_acervo(caminho)
        self.assertEqual(quantidade, 2)
        self.assertIsNone(motivo)
        self.assertIn("published_manifest", fonte)

    def test_manifesto_ausente_devolve_none_nunca_zero(self):
        quantidade, _fonte, motivo = G.urls_indexaveis_do_acervo(
            os.path.join(tempfile.gettempdir(), "nao-existe-published-manifest.jsonl"))
        self.assertIsNone(quantidade)
        self.assertEqual(motivo, "published_manifest_ausente")


class SemDadoPessoal(unittest.TestCase):
    CAMPOS_PROIBIDOS = ("remote_addr", "remote_addr_forma", "user_agent", "path",
                        "cf_ray", "referer", "rotas", "ips")

    def test_a_linha_da_serie_nao_carrega_nada_que_identifique(self):
        """O caminho da rede social carrega `?termo=` — o que o visitante buscou.
        A série é de CONTAGENS: nem o IP pseudonimizado atravessa."""
        registros = [
            linha_do_ledger(),
            linha_do_ledger(superficie="redesocial",
                            path="/redesocial/consulta/?termo=interdicao+de+idoso",
                            remote_addr="pseud_" + "c" * 32,
                            remote_addr_forma="pseudonimo_diario"),
        ]
        agregado, contadores, metodos = G.agrega(registros, FAIXAS, sem_rdns=True)
        linhas = G.monta_linhas("2026-09-05", agregado, metodos, contadores,
                                DENOMINADORES_OK, FAIXAS, True, "2026-09-05T12:00:00Z")
        bruto = json.dumps(linhas, ensure_ascii=False)
        for campo in self.CAMPOS_PROIBIDOS:
            self.assertNotIn('"%s"' % campo, bruto, "campo %r vazou para a serie" % campo)
        self.assertNotIn("interdicao", bruto)
        self.assertNotIn(IP_NA_FAIXA, bruto)
        self.assertNotIn("pseud_", bruto)


class PontaAPonta(unittest.TestCase):
    def test_executa_sobre_ledger_temporario_e_grava_serie(self):
        """O produtor inteiro, por subprocess, sobre um ledger e uma série que
        moram fora de `data/` — nenhuma execução de teste toca dado versionado.

        Usa `googlebot` com IP REAL da faixa publicada em `data/ops/bot_ip_ranges/`
        justamente para exercitar a leitura das faixas de verdade: fixture com
        faixa sintética provaria a aritmética e não provaria que o arquivo do
        operador é lido.
        """
        with tempfile.TemporaryDirectory() as tmp:
            fonte_dir = os.path.join(tmp, "access")
            os.makedirs(fonte_dir)
            with open(os.path.join(fonte_dir, "nginx-2026-09-05.jsonl"), "w",
                      encoding="utf-8") as handle:
                handle.write(json.dumps(linha_do_ledger(
                    agent_key="googlebot", remote_addr="192.178.4.1",
                    user_agent="Mozilla/5.0 (compatible; Googlebot/2.1; "
                               "+http://www.google.com/bot.html)")) + "\n")
            serie = os.path.join(tmp, "social_bot_coverage_daily.jsonl")
            saida = subprocess.run(
                [os.path.join(RAIZ, "tools/generate-social-bot-coverage"),
                 "--dia", "2026-09-05", "--sem-rdns",
                 "--fonte-dir", fonte_dir, "--serie", serie],
                capture_output=True, text=True, timeout=120)
            self.assertEqual(saida.returncode, 0, saida.stderr)
            self.assertTrue(os.path.isfile(serie), saida.stdout)
            with open(serie, encoding="utf-8") as handle:
                linhas = [json.loads(linha) for linha in handle]

        self.assertEqual(len(linhas), 2, "um agente, duas superficies")
        por_superficie = {linha["superficie"]: linha for linha in linhas}
        acervo = por_superficie["acervo"]
        self.assertEqual(acervo["schema_version"], "social_bot_coverage_daily_v1")
        self.assertEqual(acervo["agent_key"], "googlebot")
        self.assertEqual(acervo["verification_method"], "ip_range")
        self.assertEqual(acervo["requests_authentic"], 1,
                         "192.178.4.1 esta na faixa publicada do Googlebot")
        self.assertFalse(acervo["summable"], "a linha e snapshot do dia, nao delta")
        self.assertFalse(acervo["requests_is_metric"])
        self.assertIn("nginx-2026-09-05.jsonl", acervo["fonte"])
        self.assertEqual(por_superficie["redesocial"]["requests"], 0)

    def test_nao_grava_nada_com_simular(self):
        with tempfile.TemporaryDirectory() as tmp:
            fonte_dir = os.path.join(tmp, "access")
            os.makedirs(fonte_dir)
            with open(os.path.join(fonte_dir, "nginx-2026-09-05.jsonl"), "w",
                      encoding="utf-8") as handle:
                handle.write(json.dumps(linha_do_ledger(
                    agent_key="googlebot", remote_addr="192.178.4.1")) + "\n")
            serie = os.path.join(tmp, "social_bot_coverage_daily.jsonl")
            saida = subprocess.run(
                [os.path.join(RAIZ, "tools/generate-social-bot-coverage"),
                 "--dia", "2026-09-05", "--sem-rdns", "--simular",
                 "--fonte-dir", fonte_dir, "--serie", serie],
                capture_output=True, text=True, timeout=120)
            self.assertEqual(saida.returncode, 0, saida.stderr)
            self.assertFalse(os.path.exists(serie))


if __name__ == "__main__":
    unittest.main(verbosity=1)


class SerieEIdempotente(unittest.TestCase):
    """Rodar o produtor N vezes não multiplica a série por N.

    O DEFEITO MEDIDO NO DISCO, e é por isso que esta classe existe: a primeira
    versão abria a série em modo "a". Duas execuções de teste deixaram 66 chaves
    distintas em 264 linhas — cada uma quatro vezes. Quem somasse a série
    contaria quatro vezes o tráfego que existiu, e a série existe justamente
    para dizer quanto bot rastreou cada superfície.

    E as cópias não eram iguais: uma passada com --sem-rdns grava
    `verification_method: none` para yandexbot e amazonbot, e a seguinte grava
    `rdns_fcrdns`. Duas linhas para a mesma (data, agente, superfície), e nada
    no arquivo dizia qual valia.
    """

    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="serie-cobertura-")
        self.addCleanup(shutil.rmtree, self.pasta, True)
        self.serie = os.path.join(self.pasta, "cobertura.jsonl")

    def linhas(self):
        with open(self.serie, encoding="utf-8") as arquivo:
            return [json.loads(l) for l in arquivo if l.strip()]

    def test_gravar_a_mesma_chave_duas_vezes_substitui_em_vez_de_somar(self):
        primeira = {"date": "2026-09-04", "agent_key": "yandexbot", "superficie": "acervo",
                    "requests": 2, "verification_method": "none"}
        segunda = dict(primeira, verification_method="rdns_fcrdns")
        G.grava_serie(self.serie, [primeira])
        G.grava_serie(self.serie, [segunda])
        linhas = self.linhas()
        self.assertEqual(len(linhas), 1, "a segunda gravação duplicou em vez de substituir")
        self.assertEqual(linhas[0]["verification_method"], "rdns_fcrdns",
                         "a linha que sobrou tem de ser a mais recente, não a degradada")

    def test_chave_fora_do_escopo_da_execucao_SOBREVIVE(self):
        # Uma passada de janela curta não pode apagar o backfill. É por isso
        # que o produtor lê a própria saída — para PRESERVAR, nunca para
        # derivar valor nenhum.
        antiga = {"date": "2026-08-01", "agent_key": "googlebot", "superficie": "acervo",
                  "requests": 9, "verification_method": "ip_range"}
        G.grava_serie(self.serie, [antiga])
        nova = {"date": "2026-09-05", "agent_key": "googlebot", "superficie": "acervo",
                "requests": 3, "verification_method": "ip_range"}
        G.grava_serie(self.serie, [nova])
        datas = sorted(l["date"] for l in self.linhas())
        self.assertEqual(datas, ["2026-08-01", "2026-09-05"])

    def test_nenhum_valor_e_copiado_da_serie_para_a_saida(self):
        # A fronteira que separa "ler para preservar" de "ler para derivar".
        # Se o produtor copiasse valor da série, esta linha voltaria com o
        # `requests` antigo em vez do novo.
        G.grava_serie(self.serie, [{"date": "2026-09-04", "agent_key": "gptbot",
                                    "superficie": "acervo", "requests": 100,
                                    "verification_method": "ip_range"}])
        G.grava_serie(self.serie, [{"date": "2026-09-04", "agent_key": "gptbot",
                                    "superficie": "acervo", "requests": 1,
                                    "verification_method": "ip_range"}])
        self.assertEqual(self.linhas()[0]["requests"], 1)

    def test_linha_ilegivel_nao_e_apagada_em_silencio(self):
        with open(self.serie, "w", encoding="utf-8") as arquivo:
            arquivo.write("{isto nao e json}\n")
        G.grava_serie(self.serie, [{"date": "2026-09-05", "agent_key": "bingbot",
                                    "superficie": "acervo", "requests": 1,
                                    "verification_method": "ip_range"}])
        with open(self.serie, encoding="utf-8") as arquivo:
            bruto = arquivo.read()
        self.assertIn("{isto nao e json}", bruto,
                      "linha ilegível apagada em silêncio é dado perdido sem aviso")

    def test_a_serie_REAL_no_disco_nao_tem_chave_duplicada(self):
        # Amostra real, não fixture: se alguém reintroduzir o append, esta
        # asserção cai sobre o artefato versionado.
        caminho = os.path.join(RAIZ, "data", "ops", "social_bot_coverage_daily.jsonl")
        if not os.path.exists(caminho):
            self.skipTest("série ainda não gerada nesta árvore")
        vistas = collections.Counter()
        with open(caminho, encoding="utf-8") as arquivo:
            for linha in arquivo:
                if not linha.strip():
                    continue
                registro = json.loads(linha)
                vistas[tuple(registro.get(c) for c in G.CHAVE_DA_SERIE)] += 1
        duplicadas = {k: v for k, v in vistas.items() if v > 1}
        self.assertEqual(duplicadas, {}, "a série no disco tem chave duplicada")
