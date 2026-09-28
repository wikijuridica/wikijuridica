#!/usr/bin/env python3
"""Testes de tools/accessledger.py — o detector de varredura sintetica no access log.

O teste central aqui e ANTI-FALSO-POSITIVO sobre AMOSTRA REAL, como manda a regra
do repositorio ("detector novo nasce com teste de falso positivo sobre amostra
real", CLAUDE.md, secao PUBLICAR E CORRIGIR). Um detector de contaminacao de
metrica que acuse tráfego honesto e pior que nenhum: o operador aprende a ignorar
o gate, e a proxima contaminacao de verdade passa junto com os gritos falsos.

O detalhe que torna isso nao-obvio: o criterio ingenuo ("muita requisicao do
mesmo agente") acusaria o watchdog interno, que faz ~1.400 requisicoes por dia
neste log, e o `wj-urlspace-audit`, que faz 186 num minuto. Os dois sao honestos —
o primeiro se declara aquecimento, o segundo repete as mesmas rotas. Por isso o
criterio exige TRES coisas juntas (volume, taxa e razao de varredura) ou a
enumeracao do acervo, e nao apenas volume.

Rodar:
    python3 tools/test_accessledger.py
    python3 -m unittest discover -s tools -p 'test_accessledger.py'
"""

from __future__ import annotations

import datetime
import json
import os
import pathlib
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

import accessledger  # noqa: E402

# As tres varreduras do harness de smoke de 2026-08-12, identificadas pela
# auditoria linha a linha. Sao o VERDADEIRO POSITIVO que o detector tem que
# apanhar; se um dia deixarem de ser apanhadas, o gate virou enfeite.
VARREDURAS_CONHECIDAS = {
    ("access-2026-08-12.jsonl", "2026-08-12T06:32:07Z",
     "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"),
    ("access-2026-08-12.jsonl", "2026-08-12T06:32:07Z",
     "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 "
     "(KHTML, like Gecko) Chrome/99.0.4844.84 Mobile Safari/537.36 "
     "(compatible; Googlebot/2.1; +http://www.google.com/bot.html)"),
    ("access-2026-08-12.jsonl", "2026-08-12T06:34:33Z", ""),
}

# Sessoes REAIS do mesmo corpus, escolhidas por serem as que mais se parecem com
# uma varredura — as maiores em volume, em taxa e em razao de varredura. Sao o
# FALSO POSITIVO que o detector nao pode cometer.
SESSOES_REAIS_LIMITROFES = [
    # 297 linhas: a maior sessao real do corpus inteiro (razao 0,42).
    ("access-2026-08-12.jsonl", "2026-08-12T09:59:50Z", ""),
    # 186 linhas de auditoria interna de URL, 2,4 req/s (razao 0,50).
    ("access-2026-08-12.jsonl", "2026-08-12T09:40:32Z", "wj-urlspace-audit/1.0"),
    # 171 linhas com razao 1,00 — varredura de verdade, mas 56x menor que o piso.
    ("access-2026-08-07.jsonl", "2026-08-07T01:12:36Z",
     "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; "
     "Googlebot/2.1; +http://www.google.com/bot.html) Chrome/125.0.6422.175 Safari/537.36"),
]


def linha(ts, path, ua="", warming=False, simulacao=False, route_class="page"):
    return json.dumps({
        "ts": ts, "method": "GET", "path": path, "status": 200, "bytes": 20000,
        "duration_ms": 1, "route_class": route_class,
        "bot_class": "unknown_or_standard_user_agent", "bot_rule": "*",
        "user_agent": ua, "warming": warming, "bot_simulation": simulacao,
    }, ensure_ascii=False)


def instantes(inicio, quantidade, passo_s):
    base = datetime.datetime.strptime(inicio, "%Y-%m-%dT%H:%M:%SZ")
    for indice in range(quantidade):
        yield (base + datetime.timedelta(seconds=indice * passo_s)).strftime(
            "%Y-%m-%dT%H:%M:%SZ")


class CorpusReal(unittest.TestCase):
    """Amostra real: os arquivos de data/ops/access/ como estao no repo."""

    @classmethod
    def setUpClass(cls):
        cls.arquivos = accessledger.arquivos_do_ledger(str(RAIZ))
        if not cls.arquivos:
            raise unittest.SkipTest("data/ops/access/ vazio neste checkout")
        # Deteccao SEM a quarentena: o teste mede o detector, nao o estado do
        # ledger paralelo. Assim ele continua valendo depois de quarentenar.
        cls.achados, cls.acervo = accessledger.detectar(str(RAIZ))
        cls.acusadas = {
            (s["source_file"], s["ts_start"], s["user_agent"]) for s in cls.achados
        }

    def test_as_tres_varreduras_do_harness_sao_detectadas(self):
        faltando = VARREDURAS_CONHECIDAS - self.acusadas
        self.assertEqual(faltando, set(),
                         "varredura sintetica conhecida deixou de ser detectada")

    def test_nenhuma_sessao_real_limitrofe_e_acusada(self):
        for chave in SESSOES_REAIS_LIMITROFES:
            self.assertNotIn(chave, self.acusadas,
                             "falso positivo em sessao real: %s" % (chave,))

    def test_toda_acusacao_tem_forma_de_varredura(self):
        """Nenhuma acusacao pode sair com razao de varredura baixa.

        Se alguma sair, o detector estaria confundindo flood na mesma URL com
        enumeracao de acervo — problemas diferentes, donos diferentes.
        """
        for sessao in self.achados:
            self.assertGreaterEqual(
                sessao["sweep_ratio"], accessledger.MIN_RAZAO_VARREDURA,
                "acusacao sem forma de varredura: %s" % sessao["ts_start"])

    def test_watchdog_interno_nunca_entra_em_sessao(self):
        """O watchdog faz ~1.400 requisicoes/dia e se declara aquecimento."""
        for sessao in accessledger.sessoes(
                str(RAIZ / "data/ops/access/access-2026-08-12.jsonl")):
            self.assertNotIn("watchdog", sessao["user_agent"])

    def test_linhas_ja_declaradas_simulacao_ficam_fora(self):
        """As 140 linhas de Googlebot com bot_simulation:true nao geram sessao."""
        caminho = RAIZ / "data/ops/access/access-2026-08-12.jsonl"
        declaradas = 0
        for _n, _bruto, registro in accessledger.ler(str(caminho)):
            if registro and registro.get("bot_simulation"):
                declaradas += 1
        self.assertGreater(declaradas, 0, "amostra sem linha de simulacao declarada")
        em_sessao = sum(s["line_count"] for s in accessledger.sessoes(str(caminho)))
        total = sum(1 for _n, _b, r in accessledger.ler(str(caminho)) if r)
        nao_sinteticas = sum(
            1 for _n, _b, r in accessledger.ler(str(caminho))
            if r and not r.get("warming") and not r.get("bot_simulation"))
        self.assertEqual(em_sessao, nao_sinteticas)
        self.assertLess(em_sessao, total)


class Fixtures(unittest.TestCase):
    """Casos construidos: o que o corpus real ainda nao exercitou."""

    def escrever(self, linhas):
        pasta = tempfile.mkdtemp(prefix="wj-accessledger-")
        caminho = os.path.join(pasta, "access-2026-01-01.jsonl")
        with open(caminho, "w", encoding="utf-8") as handle:
            handle.write("\n".join(linhas) + "\n")
        return caminho

    def test_flood_na_mesma_url_nao_e_varredura(self):
        """5.000 requisicoes na MESMA rota, a 100 req/s, nao viram quarentena.

        Volume e taxa acima de qualquer teto, mas razao de varredura ~0. Isso e
        um problema de producao (ataque, retry em loop) e tem que continuar
        visivel, nao ser silenciado como sintetico do proprio projeto.
        """
        linhas = [linha(ts, "/contato/advogado/", "flood/1.0")
                  for ts in instantes("2026-01-01T00:00:00Z", 5000, 0.01)]
        sessoes = accessledger.sessoes(self.escrever(linhas))
        self.assertEqual(len(sessoes), 1)
        self.assertEqual(accessledger.avaliar_sessao(sessoes[0], 9835), [])

    def test_varredura_em_rajada_cai(self):
        linhas = [linha(ts, "/area/pagina-%05d/" % indice, "harness/1.0")
                  for indice, ts in enumerate(instantes("2026-01-01T00:00:00Z", 2000, 0.02))]
        sessoes = accessledger.sessoes(self.escrever(linhas))
        motivos = accessledger.avaliar_sessao(sessoes[0], 9835)
        self.assertTrue(any("varredura em rajada" in m for m in motivos), motivos)

    def test_varredura_lenta_cai_pela_cobertura(self):
        """Uma varredura estrangulada escapa do teto de TAXA, nao do de cobertura.

        6.000 URLs distintas a 2 req/s — dez vezes abaixo do piso de rajada — e
        ainda assim 61% do acervo enumerado numa sessao so. Este e o caso que o
        teto de rajada sozinho deixaria passar.
        """
        linhas = [linha(ts, "/area/pagina-%05d/" % indice, "harness-lento/1.0")
                  for indice, ts in enumerate(instantes("2026-01-01T00:00:00Z", 6000, 0.5))]
        sessoes = accessledger.sessoes(self.escrever(linhas))
        self.assertEqual(len(sessoes), 1, "gap de 0,5s nao deveria partir a sessao")
        motivos = accessledger.avaliar_sessao(sessoes[0], 9835)
        self.assertFalse(any("varredura em rajada" in m for m in motivos),
                         "2 req/s nao e rajada")
        self.assertTrue(any("enumeracao do acervo" in m for m in motivos), motivos)

    def test_sem_acervo_legivel_a_cobertura_nao_e_afirmada(self):
        """Sem denominador, o teto de cobertura e pulado — nunca inventado."""
        linhas = [linha(ts, "/area/pagina-%05d/" % indice, "harness-lento/1.0")
                  for indice, ts in enumerate(instantes("2026-01-01T00:00:00Z", 6000, 0.5))]
        sessoes = accessledger.sessoes(self.escrever(linhas))
        self.assertEqual(accessledger.avaliar_sessao(sessoes[0], 0), [],
                         "sem acervo legivel o teto de cobertura nao existe")

    def test_intervalo_maior_que_a_janela_parte_a_sessao(self):
        cedo = [linha(ts, "/a/%d/" % i, "bot/1.0")
                for i, ts in enumerate(instantes("2026-01-01T00:00:00Z", 5, 1))]
        tarde = [linha(ts, "/b/%d/" % i, "bot/1.0")
                 for i, ts in enumerate(instantes("2026-01-01T00:05:00Z", 5, 1))]
        sessoes = accessledger.sessoes(self.escrever(cedo + tarde))
        self.assertEqual(len(sessoes), 2)


class RotaBloqueadaNoIngress(unittest.TestCase):
    """O detector categorico: rota que o nginx nao entrega nao tem cliente externo.

    Este gatilho existe porque os dois estatisticos so acordam com VOLUME (>=1.000
    linhas de rajada ou >=50% do acervo). O produtor achado em 2026-08-12 emite
    TRES linhas por execucao — `/` como Googlebot, `/` como Chrome e `/metrics` —
    e passava verde por ser pequeno demais. Os testes abaixo fixam as duas metades
    do contrato: apanha UMA linha (sem piso de volume) e nao acusa quem se
    declarou sintetico nem quem ja foi reconhecido.
    """

    def raiz_com(self, linhas, nome="access-2026-01-01.jsonl"):
        raiz = tempfile.mkdtemp(prefix="wj-rota-interna-")
        pasta = pathlib.Path(raiz) / "data" / "ops" / "access"
        pasta.mkdir(parents=True)
        (pasta / nome).write_text("\n".join(linhas) + "\n", encoding="utf-8")
        return raiz

    def test_uma_unica_linha_de_metrics_ja_reprova(self):
        """Sem piso de volume: o veredito vem da topologia, nao de um limiar.

        E a diferenca que faz este detector existir — a tripla do harness de teste
        tem 1 linha de /metrics por execucao e nenhum teto de rajada a alcanca.
        """
        raiz = self.raiz_com([linha("2026-01-01T00:00:00Z", "/metrics", "",
                                    route_class="metrics")])
        achados = accessledger.detectar_rota_interna(raiz)
        self.assertEqual(len(achados), 1, achados)
        self.assertEqual(achados[0]["line_count"], 1)
        self.assertEqual(achados[0]["path"], "/metrics")

    def test_trafego_honesto_de_pagina_nao_e_acusado(self):
        """Volume alto em rota que o ingress ENTREGA nao interessa a este gatilho.

        Falso positivo aqui seria fatal: /` e as paginas do acervo sao exatamente
        o que o log deve contar como real.
        """
        linhas = [linha(ts, "/area/pagina-%05d/" % i, "Mozilla/5.0")
                  for i, ts in enumerate(instantes("2026-01-01T00:00:00Z", 3000, 0.01))]
        self.assertEqual(accessledger.detectar_rota_interna(self.raiz_com(linhas)), [])

    def test_quem_se_declara_sintetico_nao_e_acusado(self):
        """`warming` e `bot_simulation` ja resolvem o problema — nao ha o que detectar.

        E o caminho que o produtor deve passar a usar depois de corrigido; se este
        teste quebrar, a correcao do produtor vira barulho no gate.
        """
        linhas = [
            linha("2026-01-01T00:00:00Z", "/metrics", "wikijuridica-watchdog/1.0",
                  warming=True, route_class="metrics"),
            linha("2026-01-01T00:00:01Z", "/metrics", "wikijuridica-smoke/1.0",
                  simulacao=True, route_class="metrics"),
        ]
        self.assertEqual(accessledger.detectar_rota_interna(self.raiz_com(linhas)), [])

    def test_linha_ja_reconhecida_sai_da_conta(self):
        """Quarentena reconhecida neutraliza, igual ao resto do modulo."""
        bruto = linha("2026-01-01T00:00:00Z", "/metrics", "", route_class="metrics")
        raiz = self.raiz_com([bruto])
        self.assertEqual(len(accessledger.detectar_rota_interna(raiz)), 1)
        ignorados = frozenset({accessledger.sha_linha(bruto)})
        self.assertEqual(
            accessledger.detectar_rota_interna(raiz, hashes_ignorados=ignorados), [])

    def test_corpus_real_apanha_a_tripla_do_harness_de_teste(self):
        """Amostra real: as linhas de /metrics de 2026-08-12 tem que cair.

        Sao o rastro do harness Go que instancia o handler de producao
        (internal/httpserver/security_headers_test.go). Se um dia deixarem de ser
        apanhadas sem terem sido reconhecidas, o gate virou enfeite.
        """
        if not (RAIZ / "data" / "ops" / "access").is_dir():
            raise unittest.SkipTest("data/ops/access/ vazio neste checkout")
        _entradas, hashes, _problemas = accessledger.carregar_quarentena(str(RAIZ))
        achados = accessledger.detectar_rota_interna(str(RAIZ), hashes_ignorados=hashes)
        hoje = [g for g in achados if g["source_file"] == "access-2026-08-12.jsonl"]
        if not hoje:
            raise unittest.SkipTest("linhas de 2026-08-12 ja reconhecidas na quarentena")
        self.assertEqual(hoje[0]["path"], "/metrics")
        self.assertGreaterEqual(hoje[0]["line_count"], 1)


class Quarentena(unittest.TestCase):
    """A quarentena tem que se verificar sozinha, ou nao vale nada."""

    def montar(self, membros, digest=None, member_count=None):
        raiz = tempfile.mkdtemp(prefix="wj-quarentena-")
        os.makedirs(os.path.join(raiz, "data", "ops"), exist_ok=True)
        os.makedirs(accessledger.dir_membros(raiz), exist_ok=True)
        nome = "lote.txt"
        with open(os.path.join(accessledger.dir_membros(raiz), nome),
                  "w", encoding="utf-8") as handle:
            handle.write("\n".join(membros) + "\n")
        entrada = {
            "schema_version": accessledger.SCHEMA,
            "batch_id": "abc123",
            "members_file": nome,
            "member_count": member_count if member_count is not None else len(membros),
            "members_sha256": (digest if digest is not None
                               else accessledger.digest_membros(membros)),
        }
        with open(accessledger.caminho_quarentena(raiz), "w", encoding="utf-8") as handle:
            handle.write(json.dumps(entrada) + "\n")
        return raiz

    def test_lote_integro_neutraliza_os_hashes(self):
        membros = [accessledger.sha_linha("linha %d" % i) for i in range(5)]
        _e, hashes, problemas = accessledger.carregar_quarentena(self.montar(membros))
        self.assertEqual(problemas, [])
        self.assertEqual(hashes, set(membros))

    def test_lista_editada_depois_de_revisada_e_reprovada(self):
        membros = [accessledger.sha_linha("linha %d" % i) for i in range(5)]
        raiz = self.montar(membros)
        caminho = os.path.join(accessledger.dir_membros(raiz), "lote.txt")
        with open(caminho, "a", encoding="utf-8") as handle:
            handle.write(accessledger.sha_linha("linha intrusa") + "\n")
        _e, hashes, problemas = accessledger.carregar_quarentena(raiz)
        self.assertTrue(any("digest" in p for p in problemas), problemas)
        self.assertEqual(hashes, set(), "lote nao verificado nao pode excluir nada")

    def test_arquivo_de_membros_ausente_e_reprovado(self):
        membros = [accessledger.sha_linha("linha %d" % i) for i in range(3)]
        raiz = self.montar(membros)
        os.remove(os.path.join(accessledger.dir_membros(raiz), "lote.txt"))
        _e, hashes, problemas = accessledger.carregar_quarentena(raiz)
        self.assertTrue(any("ausente" in p for p in problemas), problemas)
        self.assertEqual(hashes, set())

    def test_digest_independe_da_ordem_e_preserva_duplicata(self):
        base = ["aa", "bb", "cc"]
        self.assertEqual(accessledger.digest_membros(base),
                         accessledger.digest_membros(list(reversed(base))))
        self.assertNotEqual(accessledger.digest_membros(base),
                            accessledger.digest_membros(base + ["aa"]))


class SaneamentoDoLeitor(unittest.TestCase):
    def test_quarentena_vale_mesmo_com_incluir_sinteticos(self):
        """--incluir-sinteticos mostra aquecimento; nunca ressuscita linha forjada.

        Aquecimento e simulacao sao TIPOS de trafego que o operador pode querer
        inspecionar. Linha quarentenada e outra coisa: o projeto ja reconheceu
        que ela e forjada, e nenhuma flag de leitura a traz de volta para a conta.
        """
        raiz = tempfile.mkdtemp(prefix="wj-saneamento-")
        pasta = os.path.join(raiz, "data", "ops", "access")
        os.makedirs(pasta, exist_ok=True)
        os.makedirs(accessledger.dir_membros(raiz), exist_ok=True)

        forjada = linha("2026-01-01T00:00:00Z", "/", "harness/1.0")
        aquecimento = linha("2026-01-01T00:00:01Z", "/healthz", "watchdog/1.0",
                            warming=True, route_class="health")
        real = linha("2026-01-01T00:00:02Z", "/", "Mozilla/5.0")
        with open(os.path.join(pasta, "access-2026-01-01.jsonl"), "w",
                  encoding="utf-8") as handle:
            handle.write("\n".join([forjada, aquecimento, real]) + "\n")

        membros = [accessledger.sha_linha(forjada)]
        with open(os.path.join(accessledger.dir_membros(raiz), "lote.txt"),
                  "w", encoding="utf-8") as handle:
            handle.write("\n".join(membros) + "\n")
        with open(accessledger.caminho_quarentena(raiz), "w", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "schema_version": accessledger.SCHEMA, "batch_id": "x",
                "members_file": "lote.txt", "member_count": 1,
                "members_sha256": accessledger.digest_membros(membros),
            }) + "\n")

        registros, resumo = accessledger.linhas_saneadas(raiz)
        self.assertEqual(len(registros), 1)
        self.assertEqual(resumo["quarantined_excluded"], 1)
        self.assertEqual(resumo["warming_excluded"], 1)

        registros, resumo = accessledger.linhas_saneadas(raiz, incluir_sinteticos=True)
        self.assertEqual(len(registros), 2, "aquecimento volta, forjada nao")
        self.assertEqual(resumo["quarantined_excluded"], 1)
        self.assertNotIn(
            "harness/1.0", {r.get("user_agent") for r in registros})

    def test_sonda_com_classe_propria_continua_descartada_por_bot_simulation(self):
        """O descarte e por bot_simulation, nunca por bot_class — e a prova disso.

        Desde 2026-09-01 o handler grava a sonda do internal/checks com
        bot_class "self_simulation_probe" em vez de vestir a classe do UA
        (medido em access-2026-08-30.jsonl: 89.188 linhas/dia com UA vazio
        rotuladas "unknown_or_standard_user_agent", 40.452 com UA de Googlebot
        rotuladas "valuable_search_or_user_bot"). O rotulo novo nao pode mudar
        o que este modulo exclui: a linha tem de continuar fora da conta e
        fora de sessao pelo campo bot_simulation, e voltar SO sob
        --incluir-sinteticos. Se um dia o filtro passar a olhar bot_class, este
        teste e o primeiro a cair.
        """
        raiz = tempfile.mkdtemp(prefix="wj-sonda-classe-")
        pasta = os.path.join(raiz, "data", "ops", "access")
        os.makedirs(pasta, exist_ok=True)

        sonda = json.loads(linha("2026-01-01T00:00:00Z", "/", "", simulacao=True))
        sonda["bot_class"] = "self_simulation_probe"
        sonda_vestida = json.loads(linha(
            "2026-01-01T00:00:01Z", "/",
            "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            simulacao=True))
        sonda_vestida["bot_class"] = "self_simulation_probe"
        sonda_vestida["bot_rule"] = "Googlebot"
        real = linha("2026-01-01T00:00:02Z", "/", "Mozilla/5.0")
        caminho = os.path.join(pasta, "access-2026-01-01.jsonl")
        with open(caminho, "w", encoding="utf-8") as handle:
            handle.write("\n".join([
                json.dumps(sonda, ensure_ascii=False),
                json.dumps(sonda_vestida, ensure_ascii=False),
                real]) + "\n")

        registros, resumo = accessledger.linhas_saneadas(raiz)
        self.assertEqual([r["user_agent"] for r in registros], ["Mozilla/5.0"])
        self.assertEqual(resumo["simulation_excluded"], 2)
        self.assertEqual(resumo["warming_excluded"], 0)

        # Fora de sessao tambem: o detector estatistico so olha o que nao se
        # declarou sintetico, e a classe nova nao o faz olhar de novo.
        self.assertEqual(
            sum(s["line_count"] for s in accessledger.sessoes(caminho)), 1)

        registros, resumo = accessledger.linhas_saneadas(raiz, incluir_sinteticos=True)
        self.assertEqual(len(registros), 3, "sob --incluir-sinteticos a sonda volta, rotulada")
        self.assertEqual(
            {r["bot_class"] for r in registros if r["bot_simulation"]},
            {"self_simulation_probe"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
