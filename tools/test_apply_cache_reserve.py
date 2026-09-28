#!/usr/bin/env python3
"""Testes de tools/apply-cache-reserve — o interruptor do Cache Reserve.

TODO teste roda OFFLINE: `CHAMAR` (a unica funcao que fala com a API) e trocada
por uma API de mentira que guarda o estado do interruptor e registra cada
chamada. O parser, o fluxo e a gravacao do ledger sao os de producao.

O que fica travado, e por que cada um importa:

  1. --dry-run NAO ESCREVE: nem PATCH na zona, nem linha no ledger. Um dry-run
     que gravasse ledger fabricaria "intencao" de mudanca que nunca houve.
  2. --on/--off SEM --confirmar NAO EXECUTA (exit 2), e tambem nao grava.
  3. Com --confirmar: DUAS linhas no ledger (intencao ANTES do PATCH, resultado
     DEPOIS, com a resposta real), o PATCH vai com a Global API Key (cabecalho
     X-Auth-Email), e o exit 0 so sai depois da RELEITURA mostrar o alvo.
  4. Idempotente: alvo igual ao vivo => nada escrito, nada gravado, exit 0.
  5. API recusando o PATCH (success:false) => exit 1 e a recusa gravada no
     ledger COMO VEIO. Isto importa porque a doc diz "A paid Cache Reserve plan
     is required" e a zona e Free: a primeira execucao real pode ser recusada,
     e a recusa tem de ficar registrada, nao interpretada.
  6. Leitura inicial falhando => exit 1 e ZERO escrita (nao se escreve as cegas).
  7. So token de zona (sem Global Key) => exit 2 antes de qualquer PATCH.
  8. --esvaziar com --off faz o POST em cache_reserve_clear e o registra;
     --esvaziar com --on e pedido invalido (exit 2).
  9. O canonico declara `off` e os endpoints vivem sob /cache/ -- nao sob
     /settings/, que e o caminho que "parece obvio" e devolve 400 (ver
     tiered-cache.json, 'endpoint_que_NAO_existe').

Rodar:
    python3 tools/test_apply_cache_reserve.py
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import pathlib
import shutil
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from unittest import mock

sys.dont_write_bytecode = True  # a ferramenta nao tem .py; sem isto sobra .pyc em tools/__pycache__

RAIZ = pathlib.Path(__file__).resolve().parent.parent
FERRAMENTA = RAIZ / "tools" / "apply-cache-reserve"
CANONICO = RAIZ / "ops" / "cloudflare" / "cache-reserve.json"

CRED_COMPLETA = {"CLOUDFLARE_ZONE_TOKEN": "zt-teste-nunca-em-rede",
                 "CLOUDFLARE_EMAIL": "teste@exemplo.invalid",
                 "CLOUDFLARE_API_TOKEN": "gk-teste-nunca-em-rede"}
SO_ZONA = {"CLOUDFLARE_ZONE_TOKEN": "zt-teste-nunca-em-rede"}


def envelope(result):
    return {"result": result, "success": True, "errors": [], "messages": []}


class ApiFalsa:
    """Guarda o valor do interruptor e o estado da limpeza; registra as chamadas."""

    def __init__(self, value="off", recusa_patch=None, leitura_quebrada=False):
        self.value = value
        self.modified_on = "2026-08-28T23:41:24.032957Z"
        self.recusa_patch = recusa_patch
        self.leitura_quebrada = leitura_quebrada
        self.clear = {"id": "cache_reserve_clear", "state": "Completed",
                      "start_ts": "2026-08-28T23:41:32.902257Z", "end_ts": "2026-08-29T01:46:32.649996Z"}
        self.chamadas = []

    def __call__(self, metodo, url, cabecalhos, corpo=None, timeout=45.0):
        caminho = url.split("/zones/", 1)[1].split("/", 1)[1]
        self.chamadas.append({"metodo": metodo, "caminho": caminho, "corpo": corpo,
                              "cabecalhos": dict(cabecalhos)})
        if caminho == "cache/cache_reserve":
            if metodo == "GET":
                if self.leitura_quebrada:
                    return {"success": False, "errors": [{"code": 10000, "message": "Authentication error"}],
                            "result": None}, 403
                return envelope({"id": "cache_reserve", "value": self.value,
                                 "modified_on": self.modified_on, "editable": True}), 200
            if metodo == "PATCH":
                if self.recusa_patch:
                    return {"success": False, "errors": [{"code": 1001, "message": self.recusa_patch}],
                            "result": None, "messages": []}, 400
                self.value = corpo["value"]
                self.modified_on = "2026-09-09T15:00:00.000000Z"
                return envelope({"id": "cache_reserve", "value": self.value,
                                 "modified_on": self.modified_on, "editable": True}), 200
        if caminho == "cache/cache_reserve_clear":
            if metodo == "GET":
                return envelope(dict(self.clear)), 200
            if metodo == "POST":
                self.clear = {"id": "cache_reserve_clear", "state": "In-progress",
                              "start_ts": "2026-09-09T15:00:05.000000Z", "end_ts": None}
                return envelope(dict(self.clear)), 200
        return {"success": False, "errors": [{"message": f"endpoint inesperado {metodo} {caminho}"}]}, 404

    def patches(self):
        return [c for c in self.chamadas if c["metodo"] == "PATCH"]

    def posts(self):
        return [c for c in self.chamadas if c["metodo"] == "POST"]


def raiz_temporaria(com_canonico=True):
    d = tempfile.mkdtemp(prefix="cache-reserve-apply-")
    if com_canonico:
        destino = pathlib.Path(d) / "ops" / "cloudflare"
        destino.mkdir(parents=True)
        shutil.copy(CANONICO, destino / "cache-reserve.json")
    return d


def carrega(raiz):
    """Importa a ferramenta com WIKI_ROOT apontando para a arvore temporaria.
    RAIZ e lido na importacao, por isso o ambiente entra ANTES do load."""
    with mock.patch.dict(os.environ, {"WIKI_ROOT": raiz}):
        loader = SourceFileLoader("apply_cache_reserve_teste", str(FERRAMENTA))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        modulo = importlib.util.module_from_spec(spec)
        loader.exec_module(modulo)
    return modulo


def roda(modulo, argv, api, env):
    """(rc, saida). Ambiente SO com as variaveis dadas (nenhum CLOUDFLARE_* real
    vaza para dentro do teste)."""
    limpo = {k: v for k, v in os.environ.items() if not k.startswith("CLOUDFLARE_")}
    limpo.update(env)
    modulo.CHAMAR = api
    buf = io.StringIO()
    with mock.patch.dict(os.environ, limpo, clear=True), \
            contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        rc = modulo.main(argv)
    return rc, buf.getvalue()


def ledger_de(raiz):
    caminho = pathlib.Path(raiz) / "data" / "ops" / "edge_rule_apply.jsonl"
    if not caminho.exists():
        return None
    return [json.loads(l) for l in caminho.read_text(encoding="utf-8").splitlines() if l.strip()]


class Base(unittest.TestCase):
    def setUp(self):
        self.raiz = raiz_temporaria()
        self.mod = carrega(self.raiz)

    def tearDown(self):
        shutil.rmtree(self.raiz, ignore_errors=True)


class Status(Base):
    def test_status_le_os_dois_endpoints_e_nao_escreve(self):
        api = ApiFalsa("off")
        rc, saida = roda(self.mod, ["--status"], api, CRED_COMPLETA)
        self.assertEqual(rc, 0, saida)
        self.assertIn("value='off'", saida)
        self.assertIn("bate", saida)
        self.assertIn("state='Completed'", saida)
        self.assertEqual([c["metodo"] for c in api.chamadas], ["GET", "GET"])
        self.assertIsNone(ledger_de(self.raiz))

    def test_status_com_vivo_on_diz_que_diverge(self):
        api = ApiFalsa("on")
        rc, saida = roda(self.mod, ["--status"], api, CRED_COMPLETA)
        self.assertEqual(rc, 0, saida)
        self.assertIn("DIVERGE", saida)

    def test_status_usa_o_token_de_zona_nao_a_global_key(self):
        api = ApiFalsa("off")
        roda(self.mod, ["--status"], api, CRED_COMPLETA)
        for c in api.chamadas:
            self.assertIn("Authorization", c["cabecalhos"])
            self.assertNotIn("X-Auth-Key", c["cabecalhos"])


class NaoEscreve(Base):
    def test_dry_run_nao_faz_patch_nem_grava_ledger(self):
        api = ApiFalsa("off")
        rc, saida = roda(self.mod, ["--on", "--dry-run"], api, CRED_COMPLETA)
        self.assertEqual(rc, 0, saida)
        self.assertIn("--dry-run", saida)
        self.assertIn("vai aplicar", saida)
        self.assertEqual(api.patches(), [])
        self.assertEqual(api.value, "off")
        self.assertIsNone(ledger_de(self.raiz), "dry-run gravou ledger")

    def test_dry_run_com_confirmar_continua_sem_escrever(self):
        """--dry-run vence --confirmar: quem pede simulacao nao quer escrita."""
        api = ApiFalsa("off")
        rc, saida = roda(self.mod, ["--on", "--dry-run", "--confirmar"], api, CRED_COMPLETA)
        self.assertEqual(rc, 0, saida)
        self.assertEqual(api.patches(), [])
        self.assertIsNone(ledger_de(self.raiz))

    def test_on_sem_confirmar_nao_executa_exit_2(self):
        api = ApiFalsa("off")
        rc, saida = roda(self.mod, ["--on"], api, CRED_COMPLETA)
        self.assertEqual(rc, 2, saida)
        self.assertIn("--confirmar", saida)
        self.assertEqual(api.patches(), [])
        self.assertIsNone(ledger_de(self.raiz))

    def test_idempotente_alvo_igual_ao_vivo(self):
        api = ApiFalsa("off")
        rc, saida = roda(self.mod, ["--off", "--confirmar"], api, CRED_COMPLETA)
        self.assertEqual(rc, 0, saida)
        self.assertIn("nada a fazer", saida)
        self.assertEqual(api.patches(), [])
        self.assertIsNone(ledger_de(self.raiz))

    def test_leitura_falhando_nao_escreve_as_cegas(self):
        api = ApiFalsa("off", leitura_quebrada=True)
        rc, saida = roda(self.mod, ["--on", "--confirmar"], api, CRED_COMPLETA)
        self.assertEqual(rc, 1, saida)
        self.assertIn("nao escrevo as cegas", saida)
        self.assertEqual(api.patches(), [])
        self.assertIsNone(ledger_de(self.raiz))

    def test_so_token_de_zona_nao_tenta_escrever(self):
        api = ApiFalsa("off")
        rc, saida = roda(self.mod, ["--on", "--confirmar"], api, SO_ZONA)
        self.assertEqual(rc, 2, saida)
        self.assertIn("Global API Key", saida)
        self.assertEqual(api.patches(), [])
        self.assertIsNone(ledger_de(self.raiz))

    def test_sem_credencial_sai_2(self):
        api = ApiFalsa("off")
        rc, saida = roda(self.mod, ["--status"], api, {})
        self.assertEqual(rc, 2, saida)
        self.assertIn("credencial", saida)
        self.assertEqual(api.chamadas, [])

    def test_sem_alvo_sai_2(self):
        api = ApiFalsa("off")
        rc, saida = roda(self.mod, [], api, CRED_COMPLETA)
        self.assertEqual(rc, 2, saida)

    def test_esvaziar_com_on_e_invalido(self):
        api = ApiFalsa("off")
        rc, saida = roda(self.mod, ["--on", "--esvaziar", "--confirmar"], api, CRED_COMPLETA)
        self.assertEqual(rc, 2, saida)
        self.assertEqual(api.chamadas, [])


class Escreve(Base):
    def test_on_confirmar_patch_com_global_key_e_duas_linhas_no_ledger(self):
        api = ApiFalsa("off")
        rc, saida = roda(self.mod, ["--on", "--confirmar", "--motivo", "gatilho de teste"], api, CRED_COMPLETA)
        self.assertEqual(rc, 0, saida)
        self.assertIn("APLICADO", saida)
        self.assertEqual(api.value, "on")
        patches = api.patches()
        self.assertEqual(len(patches), 1)
        self.assertEqual(patches[0]["corpo"], {"value": "on"})
        self.assertEqual(patches[0]["caminho"], "cache/cache_reserve")
        self.assertIn("X-Auth-Email", patches[0]["cabecalhos"])
        self.assertNotIn("Authorization", patches[0]["cabecalhos"])
        # Sequencia: GET (le), PATCH, GET (rele).
        self.assertEqual([c["metodo"] for c in api.chamadas], ["GET", "PATCH", "GET"])
        linhas = ledger_de(self.raiz)
        self.assertEqual(len(linhas), 2, linhas)
        intencao, resultado = linhas
        self.assertEqual(intencao["evento"], "intencao")
        self.assertEqual(intencao["fase"], "cache_reserve")
        self.assertEqual(intencao["schema_version"], "edge_rule_apply_v1")
        self.assertEqual(intencao["valor_antes"], "off")
        self.assertEqual(intencao["valor_pretendido"], "on")
        self.assertEqual(intencao["motivo"], "gatilho de teste")
        self.assertEqual(intencao["regras_antes"][0]["value"], "off")
        self.assertEqual(intencao["regras_depois_pretendidas"], [{"value": "on"}])
        self.assertEqual(resultado["evento"], "resultado")
        self.assertTrue(resultado["success"])
        self.assertEqual(resultado["http_status"], 200)
        self.assertEqual(resultado["result"]["value"], "on")

    def test_patch_recusado_sai_1_e_registra_a_recusa_como_veio(self):
        """O caso que a doc anuncia: 'A paid Cache Reserve plan is required'."""
        api = ApiFalsa("off", recusa_patch="Cache Reserve requires a paid plan")
        rc, saida = roda(self.mod, ["--on", "--confirmar"], api, CRED_COMPLETA)
        self.assertEqual(rc, 1, saida)
        self.assertIn("PATCH RECUSADO", saida)
        self.assertIn("requires a paid plan", saida)
        self.assertEqual(api.value, "off")
        linhas = ledger_de(self.raiz)
        self.assertEqual(len(linhas), 2, linhas)
        self.assertFalse(linhas[1]["success"])
        self.assertEqual(linhas[1]["http_status"], 400)
        self.assertEqual(linhas[1]["errors"], ["Cache Reserve requires a paid plan"])

    def test_off_esvaziar_desliga_e_posta_a_limpeza(self):
        api = ApiFalsa("on")
        rc, saida = roda(self.mod, ["--off", "--esvaziar", "--confirmar"], api, CRED_COMPLETA)
        self.assertEqual(rc, 0, saida)
        self.assertEqual(api.value, "off")
        self.assertEqual(len(api.patches()), 1)
        posts = api.posts()
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]["caminho"], "cache/cache_reserve_clear")
        self.assertIn("X-Auth-Email", posts[0]["cabecalhos"])
        linhas = ledger_de(self.raiz)
        self.assertEqual([l["evento"] for l in linhas], ["intencao", "resultado", "resultado"])
        self.assertEqual(linhas[2]["operacao"], "POST cache_reserve_clear")
        self.assertIn("In-progress", saida)

    def test_off_esvaziar_ja_desligado_so_limpa(self):
        api = ApiFalsa("off")
        rc, saida = roda(self.mod, ["--off", "--esvaziar", "--confirmar"], api, CRED_COMPLETA)
        self.assertEqual(rc, 0, saida)
        self.assertEqual(api.patches(), [])
        self.assertEqual(len(api.posts()), 1)
        linhas = ledger_de(self.raiz)
        self.assertEqual([l["evento"] for l in linhas], ["resultado"])


class HarnessQuebrado(unittest.TestCase):
    def test_canonico_ausente_sai_2(self):
        raiz = raiz_temporaria(com_canonico=False)
        try:
            mod = carrega(raiz)
            rc, saida = roda(mod, ["--status"], ApiFalsa("off"), CRED_COMPLETA)
        finally:
            shutil.rmtree(raiz, ignore_errors=True)
        self.assertEqual(rc, 2, saida)
        self.assertIn("canonico", saida)


class Canonico(unittest.TestCase):
    def test_declara_off_e_endpoints_sob_cache(self):
        dados = json.loads(CANONICO.read_text(encoding="utf-8"))
        self.assertEqual(dados["valor_esperado"], "off")
        self.assertEqual(dados["observado"]["value"], "off")
        for chave in ("estado", "escrita"):
            caminho = dados["endpoints"][chave]["caminho"]
            self.assertIn("/cache/cache_reserve", caminho)
            self.assertNotIn("/settings/", caminho)
        self.assertIn("cache_reserve_clear", dados["endpoints"]["limpeza_executar"]["caminho"])
        self.assertEqual(dados["endpoints"]["escrita"]["metodo"], "PATCH")
        # O que NAO foi medido tem de estar escrito como nao medido.
        self.assertIn("nunca", json.dumps(dados["interruptor_nao_medido"], ensure_ascii=False).lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
