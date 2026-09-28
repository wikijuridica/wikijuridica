#!/usr/bin/env python3
"""Prova por MUTAÇÃO o veredito de `check-perfil-por-bot` depois da correção de
2026-09-10 — quando o gate reprovava 15 agentes de 15 com a mesma frase,
"N req com UA de bot NÃO verificada pela borda (spoofing) — teto 0", aplicando
teto zero à SOMA de uma janela de oito dias.

O QUE FOI MEDIDO ANTES DE ESCREVER ESTES CASOS (sonda read-only contra a borda,
mesma FASE 2 do `tools/generate-bot-agents-daily`, na janela de retenção):

  • bingbot 2026-09-06: as 842 requisições não confirmadas vieram de UM IP,
    132.196.1.195 (US), fora dos 28 prefixos publicados pela Microsoft e sem
    PTR — enquanto 401 amostradas do MESMO User-Agent, no MESMO dia, foram
    confirmadas pela Cloudflare. Impostor real.
  • perplexitybot 2026-09-08, MESMA execução do MESMO código: 169 amostradas
    movidas para `ip_range`, de 18.97.9.96–103, os 8 prefixos oficiais. O
    coletor funciona; o zero do bingbot é resposta, não silêncio.

Daí os quatro eixos que este arquivo cobre, e cada caso mexe UMA coisa e exige
que o veredito mude por causa dela:

  (1) impostor ACIMA da linha de base  -> TEM de reprovar;
  (2) PerplexityBot com Cloudflare em 0 e faixa de IP alta -> NÃO pode reprovar,
      nem na forma v4 (a faixa confirma) nem na forma pré-v4 (indeterminado);
  (3) regressão real -> reprova, nomeando dia, país e a base ultrapassada;
  (4) série cumulativa com várias linhas no mesmo dia -> vale a ÚLTIMA, nos dois
      sentidos (última menor E última maior), nunca o máximo.

Mais dois que a correção exige e que nenhum deles cobriria: o gate é READ-ONLY
de verdade (fotografia da árvore antes/depois), e a linha de base não pode
apodrecer em silêncio.

Uso:  python3 tools/test_check_perfil_por_bot.py
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(RAIZ, "tools", "check-perfil-por-bot")
GERADOR = os.path.join(RAIZ, "tools", "generate-baseline-bot-nao-confirmado")

DIAS = ["2026-09-03", "2026-09-04", "2026-09-05", "2026-09-06"]


def autenticidade(cf, ip):
    if cf and ip:
        return "cloudflare_and_ip_range"
    if cf:
        return "cloudflare_verified_bot_category"
    if ip:
        return "ip_range_at_edge"
    return "unverifiable_at_edge"


def linha_borda(dia, agente, cf=0, ip=0, nao_confirmado=0, paises=None,
                operador=None, prefixos=0, com_perna_ip=True):
    """Uma linha da série da borda, na forma que `edgetelemetry` aceita.

    `com_perna_ip=False` produz a forma ANTERIOR ao v4 — sem
    `requests_*_ip_range` —, que é o que existe na série para os dias em que o
    produtor ainda não sabia verificar por faixa de IP. O `schema_version` cai
    junto de propósito: `edgetelemetry.avaliar_linha` só cobra as duas pernas de
    linha marcada v4, e uma linha "v4 sem as pernas" seria descartada antes de
    o gate a ver — o que testaria o descarte, não o veredito.
    """
    registro = {
        "schema_version": "edge_bot_agents_daily_v4" if com_perna_ip
                          else "edge_bot_agents_daily_v3",
        "date": dia,
        "agent_key": agente,
        "function": "search",
        "requests_sampled": cf + ip,
        "requests_estimated": cf + ip,
        "requests_local_verification": 0,
        "requests_sampled_unverified_ua": nao_confirmado,
        "requests_estimated_unverified_ua": nao_confirmado,
        "countries_unverified_ua": dict(paises or {}),
        "countries": {},
        "verified_bot_categories": {},
        "user_agent_samples": ["Mozilla/5.0 (compatible; %s/1.0)" % agente],
        "window_start": dia + "T00:00:00Z",
        "window_end": dia + "T23:59:59Z",
        "query_truncated": False,
        "sampled_dataset": True,
        "authenticity": autenticidade(cf, ip),
    }
    if com_perna_ip:
        registro.update({
            "requests_sampled_cloudflare_verified": cf,
            "requests_estimated_cloudflare_verified": cf,
            "requests_sampled_ip_range": ip,
            "requests_estimated_ip_range": ip,
            "ip_range_operator": operador,
            "ip_range_prefixes_total": prefixos,
        })
    return registro


def fotografar(raiz):
    """Tamanho + mtime_ns + sha256 de cada arquivo da árvore.

    Fotografia, e não `os.walk` contando arquivos: o defeito que isto persegue
    (BUG-236, `check-*` que grava) reescreve arquivo que JÁ existe, e uma
    contagem de nomes passaria verde por cima disso.
    """
    retrato = {}
    for pasta, _subpastas, arquivos in os.walk(raiz):
        for nome in arquivos:
            caminho = os.path.join(pasta, nome)
            estado = os.stat(caminho)
            with open(caminho, "rb") as handle:
                digesto = hashlib.sha256(handle.read()).hexdigest()
            retrato[os.path.relpath(caminho, raiz)] = (estado.st_size,
                                                       estado.st_mtime_ns, digesto)
    return retrato


class Base(unittest.TestCase):
    def setUp(self):
        self.raiz = tempfile.mkdtemp(prefix="perfil-por-bot-")
        self.addCleanup(shutil.rmtree, self.raiz, True)
        for relativo in ("data/ops/access", "data/ops/bot_ip_ranges", "content"):
            os.makedirs(os.path.join(self.raiz, relativo), exist_ok=True)
        self.serie = os.path.join(self.raiz, "data/ops/edge_bot_agents_daily.jsonl")
        self.baseline = os.path.join(self.raiz, "data/ops/baseline_bot_nao_confirmado.json")
        self.escreve_politica()
        self.escreve_faixas()
        self.escreve_access(DIAS)

    # ---------------------------------------------------------------- fixtures
    def escreve_politica(self):
        politica = {"bot_registry": [
            {"user_agent": "bingbot", "class": "valuable_search_or_user_bot",
             "rate_tier": "unlimited_no_rate_limit"},
            {"user_agent": "PerplexityBot", "class": "valuable_search_or_user_bot",
             "rate_tier": "unlimited_no_rate_limit"},
            {"user_agent": "GPTBot", "class": "training_bot",
             "rate_tier": "training_tier_aggregated"},
        ]}
        with open(os.path.join(self.raiz, "content/crawl_policy.json"), "w",
                  encoding="utf-8") as handle:
            json.dump(politica, handle, ensure_ascii=False)

    def escreve_faixas(self):
        faixas = {
            "perplexitybot.json": {
                "schema_version": "bot_ip_ranges_v1", "operator": "perplexitybot",
                "authenticates_agents": ["perplexitybot"],
                "prefixes": ["18.97.9.96/29"], "prefix_count": 1,
            },
            "bingbot.json": {
                "schema_version": "bot_ip_ranges_v1", "operator": "bingbot",
                "authenticates_agents": ["bingbot"],
                "prefixes": ["157.55.39.0/24", "207.46.13.0/24"], "prefix_count": 2,
            },
        }
        for nome, dados in faixas.items():
            with open(os.path.join(self.raiz, "data/ops/bot_ip_ranges", nome), "w",
                      encoding="utf-8") as handle:
                json.dump(dados, handle, ensure_ascii=False)

    def escreve_access(self, dias, eventos_por_dia=None):
        """Um access log por dia. A JANELA DA BORDA sai do NOME destes arquivos."""
        for dia in dias:
            caminho = os.path.join(self.raiz, "data/ops/access", "access-%s.jsonl" % dia)
            with open(caminho, "w", encoding="utf-8") as handle:
                for evento in (eventos_por_dia or {}).get(dia, []):
                    handle.write(json.dumps(evento, ensure_ascii=False) + "\n")

    def escreve_serie(self, linhas):
        with open(self.serie, "w", encoding="utf-8") as handle:
            for linha in linhas:
                handle.write(json.dumps(linha, ensure_ascii=False, sort_keys=True) + "\n")

    def escreve_baseline(self, agentes, idade_dias=0.0):
        gerado = (datetime.now(timezone.utc) - timedelta(days=idade_dias)) \
            .strftime("%Y-%m-%dT%H:%M:%SZ")
        documento = {
            "schema_version": "baseline_bot_nao_confirmado_v1",
            "generated_at": gerado,
            "fonte": "data/ops/edge_bot_agents_daily.jsonl",
            "fonte_sha256": "",
            "janela_referencia": {"inicio": DIAS[0], "fim": DIAS[-1],
                                  "dias_pedidos": len(DIAS),
                                  "dias_com_dado": len(DIAS), "datas": DIAS},
            "agentes": {nome: {"max_diario": teto, "dia_do_maximo": DIAS[0],
                               "paises_no_dia_do_maximo": {}, "mediana_diaria": 0,
                               "dias_observados": len(DIAS), "dias_com_nao_confirmado": 1,
                               "total_janela": teto, "ip_range_operator": None,
                               "ip_range_prefixes_total": 0,
                               "dias_sem_perna_faixa_ip": []}
                        for nome, teto in agentes.items()},
        }
        with open(self.baseline, "w", encoding="utf-8") as handle:
            json.dump(documento, handle, ensure_ascii=False, indent=2, sort_keys=True)

    # ------------------------------------------------------------------ runner
    def roda(self, extra=()):
        return subprocess.run(
            [sys.executable, GATE, "--raiz", self.raiz, "--dias", str(len(DIAS)), *extra],
            cwd=RAIZ, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=180)


class Veredito(Base):
    # (1) SPOOF VERDADEIRO ---------------------------------------------------
    def test_impostor_acima_da_base_reprova_e_nomeia_dia_e_pais(self):
        # A MUTAÇÃO: o caso real do bingbot em 2026-09-06 — 842 requisições de um
        # IP fora dos 28 prefixos da Microsoft, num dia em que a Cloudflare
        # confirmou 407 do mesmo User-Agent. Com a base em 100, é regressão.
        self.escreve_serie([
            linha_borda(DIAS[0], "bingbot", cf=400, operador="bingbot", prefixos=28),
            linha_borda(DIAS[3], "bingbot", cf=407, nao_confirmado=842,
                        paises={"US": 842}, operador="bingbot", prefixos=28),
        ])
        self.escreve_baseline({"bingbot": 100})
        saida = self.roda()
        self.assertEqual(saida.returncode, 1, saida.stdout + saida.stderr)
        self.assertIn("bingbot: 842 req/dia", saida.stdout)
        self.assertIn(DIAS[3], saida.stdout)
        self.assertIn("US=842", saida.stdout)
        self.assertIn("linha de base 100", saida.stdout)
        # E não pode chamar de "spoofing" o que é ausência de confirmação.
        self.assertIn("NÃO CONFIRMADA", saida.stdout)

    def test_agente_novo_sem_base_conta_como_base_zero(self):
        # Mesmo precedente de `check-baseline-testes-vermelhos`: o que não está
        # no baseline é regressão. Sem isto, bastaria um agent_key novo para
        # entrar por baixo do gate.
        self.escreve_serie([
            linha_borda(DIAS[3], "gptbot", cf=10, nao_confirmado=7, paises={"SG": 7}),
        ])
        self.escreve_baseline({"bingbot": 100})
        saida = self.roda()
        self.assertEqual(saida.returncode, 1, saida.stdout + saida.stderr)
        self.assertIn("gptbot: 7 req/dia", saida.stdout)
        self.assertIn("SEM linha de base para este agente", saida.stdout)

    # (2) PERPLEXITYBOT ------------------------------------------------------
    def test_perplexitybot_confirmado_por_faixa_de_ip_nao_reprova(self):
        # Cloudflare NUNCA verifica a Perplexity (medido 2026-09-02 e de novo em
        # 2026-09-08). Reprovar aqui seria acusar de fraude o bot que rastreia
        # todo dia de dentro da faixa que ele mesmo publica.
        #
        # A FORMA É A MEDIDA, não uma ideal: em 2026-09-08 o dia real tinha 169
        # amostradas dentro dos 8 prefixos oficiais E 34 sobrando sem
        # confirmação nenhuma (as 34 de 34.158.60.234, o host de Singapura que
        # naquele minuto também se dizia claudebot e gptbot). Um fixture com
        # residual ZERO passaria mesmo sob o teto zero antigo e não provaria
        # nada — o residual junto é o que faz este caso morder.
        self.escreve_serie(
            [linha_borda(dia, "perplexitybot", cf=0, ip=1200,
                         operador="perplexitybot", prefixos=8)
             for dia in DIAS[:3]]
            + [linha_borda(DIAS[3], "perplexitybot", cf=0, ip=169,
                           nao_confirmado=34, paises={"SG": 29},
                           operador="perplexitybot", prefixos=8)]
        )
        self.escreve_baseline({"perplexitybot": 34})
        saida = self.roda()
        self.assertEqual(saida.returncode, 0, saida.stdout + saida.stderr)
        # A perna de faixa de IP aparece NOMEADA, ao lado do residual — nunca
        # somada a ele nem escondida atrás de `requests_estimated`.
        self.assertIn("perplexitybot", saida.stdout)
        self.assertIn("max/dia=34", saida.stdout)
        self.assertIn("(+169 faixa IP)", saida.stdout)
        documento = json.loads(self.roda(["--json"]).stdout)
        perfil = documento["agentes"]["perplexitybot"]
        self.assertEqual(perfil["borda_confirmado_cloudflare"], 0)
        self.assertEqual(perfil["borda_confirmado_faixa_ip"], 3769)
        self.assertEqual(perfil["borda_nao_confirmado"], 34)
        self.assertTrue(perfil["borda_faixa_oficial_conhecida"])

    def test_perplexitybot_pre_v4_e_indeterminado_e_nao_reprova(self):
        # A MESMA medição, na forma que a série tem para os dias anteriores a
        # 2026-09-02: sem a perna de faixa de IP, o produtor nem tentou a
        # segunda verificação. Tratar aquele zero como acusação repetiria, com o
        # sinal trocado, o falso negativo que o v4 veio desfazer.
        self.escreve_serie([
            linha_borda(DIAS[3], "perplexitybot", cf=0, nao_confirmado=1200,
                        paises={"US": 1200}, com_perna_ip=False),
        ])
        self.escreve_baseline({"perplexitybot": 0})
        saida = self.roda()
        self.assertEqual(saida.returncode, 0, saida.stdout + saida.stderr)
        self.assertIn("INDETERMINADO por schema da serie", saida.stdout)
        self.assertIn("perplexitybot", saida.stdout)
        # Indeterminado NÃO é invisível: o número continua impresso.
        self.assertIn("1200", saida.stdout)

    def test_dia_cego_por_schema_nao_suspende_o_veredito_dos_dias_medidos(self):
        # DIA cego, não AGENTE cego. Se um buraco de schema na semana passada
        # suspendesse o agente inteiro, uma regressão medida HOJE sumiria — e
        # bastaria uma linha antiga para desligar o gate de um bot.
        self.escreve_serie([
            linha_borda(DIAS[0], "perplexitybot", cf=0, nao_confirmado=1200,
                        paises={"US": 1200}, com_perna_ip=False),
            linha_borda(DIAS[3], "perplexitybot", cf=0, ip=100, nao_confirmado=90,
                        paises={"SG": 90}, operador="perplexitybot", prefixos=8),
        ])
        self.escreve_baseline({"perplexitybot": 34})
        saida = self.roda()
        self.assertEqual(saida.returncode, 1, saida.stdout + saida.stderr)
        # O dia cego é declarado…
        self.assertIn("INDETERMINADO por schema da serie", saida.stdout)
        self.assertIn(DIAS[0], saida.stdout)
        # …e o dia MEDIDO reprova, com o número dele e não com o do dia cego.
        self.assertIn("perplexitybot: 90 req/dia", saida.stdout)
        self.assertIn(DIAS[3], saida.stdout)
        self.assertIn("SG=90", saida.stdout)
        self.assertNotIn("perplexitybot: 1200 req/dia", saida.stdout)

    # (3) REGRESSÃO x PATAMAR JÁ CONHECIDO -----------------------------------
    def test_igual_a_base_nao_reprova_e_o_numero_continua_visivel(self):
        # O teto zero antigo reprovava por UMA requisição. O critério novo é
        # REGRESSÃO: igual à base passa — e, se o número sumisse do relatório,
        # teríamos trocado um gate ruidoso por um gate cego.
        self.escreve_serie([
            linha_borda(DIAS[3], "bingbot", cf=400, nao_confirmado=842,
                        paises={"US": 842}, operador="bingbot", prefixos=28),
        ])
        self.escreve_baseline({"bingbot": 842})
        saida = self.roda()
        self.assertEqual(saida.returncode, 0, saida.stdout + saida.stderr)
        self.assertIn("NAO CONFIRMADO na borda, por dia", saida.stdout)
        self.assertIn("max/dia=842", saida.stdout)
        self.assertIn("base=842", saida.stdout)

    def test_soma_da_janela_nao_e_criterio(self):
        # O DEFEITO ARITMÉTICO ORIGINAL: 842+158 = 1.000 reprovava contra um teto
        # absoluto. Nenhum dos dois dias passa da base de 842, então o veredito
        # é verde — e a soma continua impressa, na coluna que diz que é soma.
        self.escreve_serie([
            linha_borda(DIAS[2], "bingbot", cf=337, nao_confirmado=158,
                        paises={"US": 158}, operador="bingbot", prefixos=28),
            linha_borda(DIAS[3], "bingbot", cf=407, nao_confirmado=842,
                        paises={"US": 842}, operador="bingbot", prefixos=28),
        ])
        self.escreve_baseline({"bingbot": 842})
        saida = self.roda()
        self.assertEqual(saida.returncode, 0, saida.stdout + saida.stderr)
        saida_json = self.roda(["--json"])
        documento = json.loads(saida_json.stdout)
        self.assertEqual(documento["agentes"]["bingbot"]["borda_nao_confirmado"], 1000)
        self.assertEqual(
            documento["agentes"]["bingbot"]["borda_nao_confirmado_max_diario"], 842)

    # (4) SÉRIE CUMULATIVA: A ÚLTIMA LINHA DO DIA VENCE ----------------------
    def test_dedup_mantem_a_ultima_linha_quando_ela_e_MENOR(self):
        # Se a dedup pegasse o MÁXIMO (era o que este check fazia até 2026-08-28),
        # aqui ela leria 900 e reprovaria contra a base 100.
        self.escreve_serie([
            linha_borda(DIAS[3], "bingbot", cf=400, nao_confirmado=900,
                        paises={"US": 900}, operador="bingbot", prefixos=28),
            linha_borda(DIAS[3], "bingbot", cf=400, nao_confirmado=0,
                        operador="bingbot", prefixos=28),
        ])
        self.escreve_baseline({"bingbot": 100})
        saida = self.roda()
        self.assertEqual(saida.returncode, 0, saida.stdout + saida.stderr)
        documento = json.loads(self.roda(["--json"]).stdout)
        self.assertEqual(documento["agentes"]["bingbot"]["borda_nao_confirmado"], 0)

    def test_dedup_mantem_a_ultima_linha_quando_ela_e_MAIOR(self):
        # A direção oposta, que uma dedup por MÍNIMO passaria: a última linha do
        # dia é a maior, e é ela que vale.
        self.escreve_serie([
            linha_borda(DIAS[3], "bingbot", cf=400, nao_confirmado=0,
                        operador="bingbot", prefixos=28),
            linha_borda(DIAS[3], "bingbot", cf=400, nao_confirmado=900,
                        paises={"US": 900}, operador="bingbot", prefixos=28),
        ])
        self.escreve_baseline({"bingbot": 100})
        saida = self.roda()
        self.assertEqual(saida.returncode, 1, saida.stdout + saida.stderr)
        self.assertIn("bingbot: 900 req/dia", saida.stdout)

    # LINHA DE BASE COMO INSTRUMENTO -----------------------------------------
    def test_baseline_ausente_reprova_e_ensina_o_comando(self):
        self.escreve_serie([linha_borda(DIAS[3], "bingbot", cf=400,
                                        operador="bingbot", prefixos=28)])
        saida = self.roda()
        self.assertEqual(saida.returncode, 1, saida.stdout + saida.stderr)
        self.assertIn("linha de base ausente", saida.stdout)
        self.assertIn("generate-baseline-bot-nao-confirmado", saida.stdout)

    def test_baseline_vencido_reprova(self):
        # Instrumento que apodrece cega o gate — e cegueira silenciosa é o
        # defeito que este arquivo inteiro existe para impedir.
        self.escreve_serie([linha_borda(DIAS[3], "bingbot", cf=400,
                                        operador="bingbot", prefixos=28)])
        self.escreve_baseline({"bingbot": 842}, idade_dias=45)
        saida = self.roda()
        self.assertEqual(saida.returncode, 1, saida.stdout + saida.stderr)
        self.assertIn("acima do teto de 30", saida.stdout)

    def test_baseline_recente_dentro_do_teto_nao_reprova(self):
        # Falso positivo do critério de idade: 29 dias ainda vale.
        self.escreve_serie([linha_borda(DIAS[3], "bingbot", cf=400,
                                        operador="bingbot", prefixos=28)])
        self.escreve_baseline({"bingbot": 842}, idade_dias=29)
        saida = self.roda()
        self.assertEqual(saida.returncode, 0, saida.stdout + saida.stderr)

    # JANELA -----------------------------------------------------------------
    def test_janela_vem_do_nome_do_access_log_e_nao_engole_a_serie_inteira(self):
        # O DEFEITO: a janela vinha dos dias em que a ORIGEM viu tráfego real de
        # bot. Como a borda absorve o acervo, a origem quase nunca vê nada — e
        # conjunto vazio virava "sem filtro", agregando a série inteira contra um
        # relatório que anuncia N dias. Aqui há um dia FORA da janela com volume
        # que reprovaria; ele não pode entrar.
        self.escreve_serie([
            linha_borda("2026-08-01", "bingbot", cf=1, nao_confirmado=5000,
                        paises={"US": 5000}, operador="bingbot", prefixos=28),
            linha_borda(DIAS[3], "bingbot", cf=400, nao_confirmado=10,
                        paises={"US": 10}, operador="bingbot", prefixos=28),
        ])
        self.escreve_baseline({"bingbot": 100})
        saida = self.roda()
        self.assertEqual(saida.returncode, 0, saida.stdout + saida.stderr)
        documento = json.loads(self.roda(["--json"]).stdout)
        self.assertEqual(documento["janela_da_borda"], DIAS)
        self.assertEqual(documento["agentes"]["bingbot"]["borda_nao_confirmado"], 10)

    # READ-ONLY --------------------------------------------------------------
    def test_o_check_nao_escreve_nada(self):
        # Precedente BUG-236: seis `check-*` desta casa gravavam dado permanente.
        # `check-*` é read-only, e isso se prova, não se declara.
        self.escreve_serie([
            linha_borda(DIAS[3], "bingbot", cf=400, nao_confirmado=842,
                        paises={"US": 842}, operador="bingbot", prefixos=28),
        ])
        self.escreve_baseline({"bingbot": 100})
        antes = fotografar(self.raiz)
        saida = self.roda()
        self.assertEqual(saida.returncode, 1, saida.stdout + saida.stderr)
        depois = fotografar(self.raiz)
        self.assertEqual(antes, depois,
                         "check-perfil-por-bot alterou a arvore: %s"
                         % sorted(set(antes.items()) ^ set(depois.items())))


class Gerador(Base):
    """A linha de base é o instrumento do veredito; ela também nasce provada."""

    def roda_gerador(self, extra=()):
        return subprocess.run(
            [sys.executable, GERADOR, "--raiz", self.raiz, "--dias", str(len(DIAS)), *extra],
            cwd=RAIZ, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=180)

    def test_baseline_registra_o_maximo_diario_e_nao_a_soma(self):
        # Se registrasse a soma (1.000), o gate toleraria um dia único de 999 —
        # que é uma regressão de 18% sobre o pior dia já visto.
        self.escreve_serie([
            linha_borda(DIAS[2], "bingbot", cf=337, nao_confirmado=158,
                        paises={"US": 158}, operador="bingbot", prefixos=28),
            linha_borda(DIAS[3], "bingbot", cf=407, nao_confirmado=842,
                        paises={"US": 842}, operador="bingbot", prefixos=28),
        ])
        saida = self.roda_gerador()
        self.assertEqual(saida.returncode, 0, saida.stdout + saida.stderr)
        with open(self.baseline, encoding="utf-8") as handle:
            documento = json.load(handle)
        bingbot = documento["agentes"]["bingbot"]
        self.assertEqual(bingbot["max_diario"], 842)
        self.assertEqual(bingbot["total_janela"], 1000)
        self.assertEqual(bingbot["dia_do_maximo"], DIAS[3])
        self.assertEqual(bingbot["paises_no_dia_do_maximo"], {"US": 842})

    def test_dry_run_nao_grava(self):
        self.escreve_serie([linha_borda(DIAS[3], "bingbot", cf=400,
                                        nao_confirmado=5, paises={"US": 5},
                                        operador="bingbot", prefixos=28)])
        antes = fotografar(self.raiz)
        saida = self.roda_gerador(["--dry-run"])
        self.assertEqual(saida.returncode, 0, saida.stdout + saida.stderr)
        self.assertIn("--dry-run: NADA foi gravado.", saida.stdout)
        self.assertEqual(antes, fotografar(self.raiz))

    def test_o_baseline_gerado_e_aceito_pelo_gate_no_mesmo_dado(self):
        # Fecha o ciclo: gerador -> arquivo -> gate. Sem isto, um par de
        # esquemas divergentes passaria em dois testes verdes e falharia junto.
        self.escreve_serie([
            linha_borda(DIAS[3], "bingbot", cf=407, nao_confirmado=842,
                        paises={"US": 842}, operador="bingbot", prefixos=28),
        ])
        self.assertEqual(self.roda_gerador().returncode, 0)
        saida = subprocess.run(
            [sys.executable, GATE, "--raiz", self.raiz, "--dias", str(len(DIAS))],
            cwd=RAIZ, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=180)
        self.assertEqual(saida.returncode, 0, saida.stdout + saida.stderr)
        self.assertIn("max/dia=842", saida.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
