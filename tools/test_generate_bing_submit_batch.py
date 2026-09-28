#!/usr/bin/env python3
"""Prova, SEM nenhuma requisicao de rede, a selecao e o ledger de
`generate-bing-submit-batch` (2026-09-09).

Rede substituida por `busca` (GET da cota) e `envia` (POST do lote) injetados
em `main(...)`; manifesto, serie do Bing e ledger apontam para um diretorio
temporario por teste.

PROVA POR MUTACAO. `test_submetida_ha_menos_de_30_dias_nao_entra` e o teste que
tranca a regra "nunca submete a mesma URL duas vezes em 30 dias": ele fica
vermelho se a linha `if aceita_em is not None and (hoje - aceita_em).days <
janela: return None` de `classifica` for removida. Para ver o vermelho sem
tocar na ferramenta, aponte a variavel `WIKI_BING_SUBMIT_ALVO` para uma copia
mutada:

  cp tools/generate-bing-submit-batch /tmp/x && sed -i '/aceita_em).days < janela/,+1d' /tmp/x
  WIKI_BING_SUBMIT_ALVO=/tmp/x python3 tools/test_generate_bing_submit_batch.py

Os demais testes trancam: a ordem de prioridade (nunca rastreada > sem url_info
> rastreio antigo > rastreada e nunca submetida), o minimo entre --max, cota
diaria, cota mensal e o teto de 500 do lote, o ledger com http_status e
resposta, a falha de POST que NAO conta para os 30 dias, e os codigos de saida.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import importlib.util
import io
import json
import os
import pathlib
import tempfile
import re
import unittest
import urllib.error
from importlib.machinery import SourceFileLoader

RAIZ = pathlib.Path(__file__).resolve().parent.parent
_ALVO = os.environ.get("WIKI_BING_SUBMIT_ALVO") or str(RAIZ / "tools" / "generate-bing-submit-batch")
BASE = "https://exemplo.test"
HOJE = dt.datetime(2026, 9, 9, 3, 10, tzinfo=dt.timezone.utc)


def _carrega_modulo_fresco():
    loader = SourceFileLoader("generate_bing_submit_batch_test_subject", _ALVO)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


def _dias_atras(n):
    return (HOJE - dt.timedelta(days=n)).date().isoformat()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        raiz = pathlib.Path(self.tmp.name)
        self.m = _carrega_modulo_fresco()
        self.m.SITE = raiz / "site.json"
        self.m.MANIFESTO = raiz / "published_manifest.jsonl"
        self.m.SERIE = raiz / "bing_webmaster_daily.jsonl"
        self.m.LEDGER = raiz / "bing_submit_ledger.jsonl"
        self.m.ENV_LOCAL = raiz / ".env.local"
        self.m.SITE.write_text(json.dumps({"base_url": BASE}), encoding="utf-8")
        os.environ[self.m.CHAVE] = "chave-de-teste"
        self.cota = {"DailyQuota": 100, "MonthlyQuota": 2200}
        self.posts = []
        self.resposta_post = (200, '{"d":null}')

    def tearDown(self):
        os.environ.pop(self.m.CHAVE, None)
        self.tmp.cleanup()

    # --- fixtures -----------------------------------------------------------
    def manifesto(self, paginas):
        """paginas: lista de (path, approved_at)."""
        with open(self.m.MANIFESTO, "w", encoding="utf-8") as h:
            for i, (path, aprovada) in enumerate(paginas):
                h.write(json.dumps({"unique_intent_id": f"int-{i}", "path": path,
                                    "canonical_url": BASE + path, "page_status": "published",
                                    "index_policy": "index", "approved_at": aprovada}) + "\n")

    def url_info(self, path, rastreada_em, coletado_em="2026-09-08T03:00:00+00:00"):
        with open(self.m.SERIE, "a", encoding="utf-8") as h:
            h.write(json.dumps({"schema": "bing_webmaster_v1", "tipo": "url_info", "Url": BASE + path,
                                "LastCrawledDate": rastreada_em, "DiscoveryDate": rastreada_em,
                                "DocumentSize": 100, "HttpStatus": 0, "coletado_em": coletado_em}) + "\n")

    def submissao(self, path, dias_atras, aceita=True):
        with open(self.m.LEDGER, "a", encoding="utf-8") as h:
            h.write(json.dumps({"schema": "bing_submit_v1", "tipo": "submissao", "url": BASE + path,
                                "submetido_em": (HOJE - dt.timedelta(days=dias_atras)).isoformat(),
                                "http_status": 200 if aceita else 500, "aceita": aceita}) + "\n")

    # --- rede falsa ---------------------------------------------------------
    def busca(self, url):
        if "GetUrlSubmissionQuota" in url:
            return {"d": dict(self.cota, __type="UrlSubmissionQuota:#Microsoft.Bing.Webmaster.Api")}
        raise AssertionError(f"GET inesperado: {url}")

    def envia(self, url, corpo):
        self.posts.append((url, corpo))
        return self.resposta_post

    def roda(self, argv):
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            codigo = self.m.main(argv, busca=self.busca, envia=self.envia, agora=HOJE)
        return codigo, saida.getvalue()

    def ledger(self):
        if not self.m.LEDGER.exists():
            return []
        return [json.loads(l) for l in self.m.LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]

    def lote(self, maximo=100):
        paginas = self.m.carrega_paginas()
        infos = self.m.ultimo_url_info()
        aceitas = self.m.ultima_submissao_aceita()
        selecionadas, contagem = self.m.seleciona(paginas, infos, aceitas, HOJE.date(), maximo)
        return [(u.replace(BASE, ""), motivo) for u, motivo, _ in selecionadas], contagem


class TestSelecao(Base):
    def test_submetida_ha_menos_de_30_dias_nao_entra(self):
        # A regra que a mutacao derruba: URL aceita ha 10 dias fica fora, ainda
        # que o Bing nunca a tenha rastreado; aceita ha 30 dias volta a concorrer.
        self.manifesto([("/a/", "2026-08-01"), ("/b/", "2026-08-01"), ("/c/", "2026-08-01")])
        self.url_info("/a/", None)
        self.url_info("/b/", None)
        self.url_info("/c/", None)
        self.submissao("/a/", dias_atras=10)
        self.submissao("/b/", dias_atras=30)
        selecionadas, contagem = self.lote()
        self.assertEqual([p for p, _ in selecionadas], ["/b/", "/c/"])
        self.assertNotIn("/a/", [p for p, _ in selecionadas])
        self.assertEqual(contagem, {"nunca_rastreada": 2})
        self.assertIsNone(self.m.classifica(BASE + "/a/", {"path": "/a/", "approved_at": "2026-08-01"},
                                            {"LastCrawledDate": None}, HOJE.date() - dt.timedelta(days=29),
                                            HOJE.date()))

    def test_submissao_recusada_nao_conta_para_os_30_dias(self):
        self.manifesto([("/a/", "2026-08-01")])
        self.url_info("/a/", None)
        self.submissao("/a/", dias_atras=1, aceita=False)
        selecionadas, _ = self.lote()
        self.assertEqual([p for p, _ in selecionadas], ["/a/"])

    def test_ordem_de_prioridade_e_desempate_determinista(self):
        self.manifesto([
            ("/recente-nunca-submetida/", "2026-08-01"),   # rastreada ha 3 dias, nunca submetida -> 3
            ("/rastreio-antigo/", "2026-08-01"),           # rastreada ha 45 dias -> 2
            ("/sem-info-nova/", "2026-08-20"),             # sem url_info, publicada depois -> 1
            ("/sem-info-velha/", "2026-08-05"),            # sem url_info, publicada antes -> 1
            ("/nunca-b/", "2026-08-10"),                   # nunca rastreada -> 0
            ("/nunca-a/", "2026-08-10"),                   # nunca rastreada, mesma data -> 0 (sha256 desempata)
            ("/nunca-mais-velha/", "2026-08-06"),          # nunca rastreada, publicada antes -> 0, primeira
            ("/recente-ja-submetida/", "2026-08-01"),      # rastreada ha 3 dias, aceita ha 40 dias -> fora
        ])
        self.url_info("/recente-nunca-submetida/", _dias_atras(3))
        self.url_info("/rastreio-antigo/", _dias_atras(45))
        self.url_info("/nunca-b/", None)
        self.url_info("/nunca-a/", None)
        self.url_info("/nunca-mais-velha/", None)
        self.url_info("/recente-ja-submetida/", _dias_atras(3))
        self.submissao("/recente-ja-submetida/", dias_atras=40)

        selecionadas, contagem = self.lote()
        import hashlib
        ha, hb = (hashlib.sha256(p.encode()).hexdigest() for p in ("/nunca-a/", "/nunca-b/"))
        empate = ["/nunca-a/", "/nunca-b/"] if ha < hb else ["/nunca-b/", "/nunca-a/"]
        self.assertEqual([p for p, _ in selecionadas],
                         ["/nunca-mais-velha/"] + empate + ["/sem-info-velha/", "/sem-info-nova/",
                                                             "/rastreio-antigo/", "/recente-nunca-submetida/"])
        self.assertEqual(dict(selecionadas)["/nunca-mais-velha/"], "nunca_rastreada")
        self.assertEqual(dict(selecionadas)["/sem-info-velha/"], "sem_url_info")
        self.assertEqual(dict(selecionadas)["/rastreio-antigo/"], "rastreio_antigo")
        self.assertEqual(dict(selecionadas)["/recente-nunca-submetida/"], "rastreada_nunca_submetida")
        self.assertEqual(contagem, {"nunca_rastreada": 3, "sem_url_info": 2, "rastreio_antigo": 1,
                                    "rastreada_nunca_submetida": 1})
        # Rastreada ha 3 dias com aceite antigo: nem (a) nem (b).
        self.assertNotIn("/recente-ja-submetida/", [p for p, _ in selecionadas])

    def test_ultima_observacao_por_url_vence(self):
        self.manifesto([("/a/", "2026-08-01")])
        self.url_info("/a/", None, coletado_em="2026-09-01T00:00:00+00:00")
        self.url_info("/a/", _dias_atras(2), coletado_em="2026-09-08T00:00:00+00:00")
        selecionadas, contagem = self.lote()
        self.assertEqual(contagem, {"rastreada_nunca_submetida": 1})
        self.assertEqual(dict(selecionadas)["/a/"], "rastreada_nunca_submetida")

    def test_teto_e_o_minimo_entre_max_cota_diaria_cota_mensal_e_500(self):
        t = self.m.teto_do_lote
        self.assertEqual(t(100, 100, 2200), 100)
        self.assertEqual(t(100, 37, 2200), 37)
        self.assertEqual(t(100, 100, 12), 12)
        self.assertEqual(t(1000, 10000, 100000), 500)
        self.assertEqual(t(100, 0, 2200), 0)
        self.assertEqual(t(30, 100, 2200), 30)


class TestExecucao(Base):
    def test_dry_run_lista_le_a_cota_e_nao_grava(self):
        self.manifesto([("/a/", "2026-08-01"), ("/b/", "2026-08-01")])
        codigo, saida = self.roda(["--dry-run"])
        self.assertEqual(codigo, 0)
        self.assertIn("cota ao vivo: 100/dia, 2200/mes", saida)
        self.assertIn(f"sem_url_info               {BASE}/a/", saida)
        self.assertIn("--dry-run", saida)
        self.assertEqual(self.posts, [])
        self.assertEqual(self.ledger(), [])

    def test_dry_run_sem_credencial_lista_com_o_max_e_sai_0(self):
        os.environ.pop(self.m.CHAVE, None)
        self.manifesto([("/a/", "2026-08-01")])
        codigo, saida = self.roda(["--dry-run", "--max", "1"])
        self.assertEqual(codigo, 0)
        self.assertIn("sem credencial", saida)
        codigo, saida = self.roda(["--max", "1"])
        self.assertEqual(codigo, 2, "submissao real sem credencial e 2")
        self.assertEqual(self.posts, [])

    def test_submete_um_lote_json_e_grava_o_ledger(self):
        self.manifesto([("/a/", "2026-08-01"), ("/b/", "2026-08-02"), ("/c/", "2026-08-03")])
        self.cota = {"DailyQuota": 2, "MonthlyQuota": 2200}
        codigo, saida = self.roda(["--max", "100"])
        self.assertEqual(codigo, 0)
        self.assertEqual(len(self.posts), 1)
        url_post, corpo = self.posts[0]
        self.assertTrue(url_post.startswith(self.m.BASE + "/SubmitUrlBatch?apikey="))
        self.assertEqual(corpo, {"siteUrl": BASE + "/", "urlList": [BASE + "/a/", BASE + "/b/"]},
                         "formato da doc oficial: siteUrl com barra final e urlList")
        linhas = self.ledger()
        self.assertEqual([l["url"] for l in linhas], [BASE + "/a/", BASE + "/b/"])
        for l in linhas:
            self.assertEqual(l["schema"], "bing_submit_v1")
            self.assertEqual(l["tipo"], "submissao")
            self.assertEqual(l["http_status"], 200)
            self.assertTrue(l["aceita"])
            self.assertEqual(l["resposta"], '{"d":null}')
            self.assertEqual(l["submetido_em"], HOJE.isoformat())
            self.assertEqual(l["cota_diaria"], 2)
            self.assertEqual(l["motivo"], "sem_url_info")
        self.assertEqual(len({l["lote_id"] for l in linhas}), 1)

        # No dia seguinte as duas aceitas ficam fora e so /c/ concorre.
        self.posts.clear()
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            codigo = self.m.main(["--max", "100"], busca=self.busca, envia=self.envia,
                                 agora=HOJE + dt.timedelta(days=1))
        self.assertEqual(codigo, 0)
        self.assertEqual(self.posts[0][1]["urlList"], [BASE + "/c/"])

    def test_post_recusado_fica_no_ledger_com_aceita_false_e_sai_1(self):
        self.manifesto([("/a/", "2026-08-01")])
        self.resposta_post = (404, "Endpoint not found")
        codigo, saida = self.roda([])
        self.assertEqual(codigo, 1)
        self.assertIn("RECUSADO", saida)
        linhas = self.ledger()
        self.assertEqual(len(linhas), 1)
        self.assertEqual(linhas[0]["http_status"], 404)
        self.assertFalse(linhas[0]["aceita"])
        self.assertEqual(linhas[0]["resposta"], "Endpoint not found")
        # E amanha ela volta: a recusa nao conta para os 30 dias.
        self.resposta_post = (200, '{"d":null}')
        self.posts.clear()
        codigo, _ = self.roda([])
        self.assertEqual(codigo, 0)
        self.assertEqual(self.posts[0][1]["urlList"], [BASE + "/a/"])

    def test_cota_ilegivel_sai_2_sem_submeter(self):
        self.manifesto([("/a/", "2026-08-01")])

        def fora(url):
            raise urllib.error.URLError("rede fora")

        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            codigo = self.m.main([], busca=fora, envia=self.envia, agora=HOJE)
        self.assertEqual(codigo, 2)
        self.assertEqual(self.posts, [])
        self.assertEqual(self.ledger(), [])

    def test_nada_a_submeter_sai_0_sem_post(self):
        self.manifesto([("/a/", "2026-08-01")])
        self.submissao("/a/", dias_atras=2)
        codigo, saida = self.roda([])
        self.assertEqual(codigo, 0)
        self.assertIn("nada a submeter", saida)
        self.assertEqual(self.posts, [])


class IdentidadeDeSaida(unittest.TestCase):
    """Exercita os DOIS caminhos reais de rede: o GET da cota (`busca_json`) e
    o POST do lote (`envia_json`).

    Os demais testes injetam `busca` e `envia` e por isso nunca viram um
    cabecalho — foi por esse buraco que o POST que PEDE rastreio ao Bing saiu
    como `Python-urllib/3.x`. Aqui a rede e' dublada em
    `urllib.request.urlopen`, um nivel abaixo do que a ferramenta monta.

    PROVA POR MUTACAO: apagar o `User-Agent` de qualquer um dos dois deixa este
    teste vermelho. Para ver sem tocar na ferramenta:

      cp tools/generate-bing-submit-batch /tmp/x
      sed -i 's/,\n *"User-Agent": USER_AGENT//' /tmp/x   # ou remova a linha a mao
      WIKI_BING_SUBMIT_ALVO=/tmp/x python3 tools/test_generate_bing_submit_batch.py
    """

    CANONICO = re.compile(
        r"^Mozilla/5\.0 \(compatible; WikijuridicaBot/\d+\.\d+; "
        r"\+https://wikijuridica\.com\.br/bot/; [a-z0-9][a-z0-9 .,:/-]*\)$")

    def setUp(self):
        self.m = _carrega_modulo_fresco()

    @contextlib.contextmanager
    def _urlopen_dublado(self, corpo=b'{"d": null}'):
        capturadas = []

        class RespostaFalsa(io.BytesIO):
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *_):
                self.close()
                return False

        def falso_urlopen(requisicao, timeout=None):
            capturadas.append(requisicao)
            return RespostaFalsa(corpo)

        original = self.m.urllib.request.urlopen
        self.m.urllib.request.urlopen = falso_urlopen
        try:
            yield capturadas
        finally:
            self.m.urllib.request.urlopen = original

    def _confere(self, requisicao):
        enviado = requisicao.get_header("User-agent")
        self.assertIsNotNone(enviado, "saiu sem User-Agent: o urllib mandaria Python-urllib")
        self.assertNotIn("Python-urllib", enviado)
        self.assertRegex(enviado, self.CANONICO)
        return enviado

    def test_get_da_cota_sai_como_wikijuridicabot(self):
        with self._urlopen_dublado(b'{"d": {"DailyQuota": 100, "MonthlyQuota": 2200}}') as pedidos:
            self.m.busca_json("https://ssl.bing.com/webmaster/api.svc/json/GetUrlSubmissionQuota")
        self.assertEqual(len(pedidos), 1)
        self._confere(pedidos[0])

    def test_post_do_lote_sai_como_wikijuridicabot(self):
        with self._urlopen_dublado() as pedidos:
            status, _ = self.m.envia_json(
                "https://ssl.bing.com/webmaster/api.svc/json/SubmitUrlBatch",
                {"siteUrl": "https://wikijuridica.com.br/", "urlList": ["https://wikijuridica.com.br/a/"]})
        self.assertEqual(status, 200)
        self.assertEqual(len(pedidos), 1)
        self.assertEqual(pedidos[0].get_method(), "POST")
        self._confere(pedidos[0])

    def test_proposito_descreve_submissao_e_nao_leitura(self):
        """Cabecalho que mente sobre o proposito e' pior que UA escrito a mao
        (internal/wikijuridicabot/bot.go). Esta saida submete URL; ela nao le
        metadado de demanda, entao nao toma emprestado o proposito do coletor."""
        self.assertTrue(self.m.USER_AGENT.endswith("; submissao-de-url)"), self.m.USER_AGENT)
        self.assertNotIn("observacao-de-demanda", self.m.USER_AGENT)

    def test_nao_se_apresenta_como_navegador_nem_como_bot_de_terceiro(self):
        for proibido in ("Chrome/", "Safari/", "Firefox/", "Edg/",
                         "Googlebot", "bingbot", "GPTBot", "ClaudeBot"):
            self.assertNotIn(proibido, self.m.USER_AGENT)


if __name__ == "__main__":
    unittest.main()
