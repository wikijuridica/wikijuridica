#!/usr/bin/env python3
"""Testes de tools/check-edge-tiered-drift — o gate dos dois interruptores de tiered cache.

TODO teste aqui roda OFFLINE. Nenhum toca a API viva: um gate de infraestrutura
cujo teste depende de rede vira um teste que ninguem roda, e o proprio defeito
que este gate evita (indisponibilidade lida como veredito) reapareceria dentro da
suite.

O PESO ESTA NOS FALSOS POSITIVOS, e cada um deles reprova um comportamento errado
concreto, nao apenas confirma o certo:

  1. METADADO QUE MUDA SOZINHO. `modified_on` muda a cada mexida de painel e
     `editable` MENTE -- o interruptor mestre responde `editable:false` e mesmo
     assim aceita PATCH (medido em 2026-08-12: success:true, valor mudou, editable
     continuou false). Um gate que comparasse o objeto inteiro gritaria falso toda
     semana, e o operador aprenderia a ignora-lo. O teste monta o estado REAL de
     producao -- mestre com editable:false -- e exige verde.

  2. SEM CREDENCIAL. Maquina sem .env.local nao esta em drift, esta sem
     instrumento. Reprovar por isso ja foi defeito medido neste repositorio
     (check-edge-vary-contract diagnosticava tunel oscilando como envenenamento
     de cache). Exige exit 0 E `verificada:false` -- as duas coisas, porque exit 0
     sozinho seria indistinguivel de aprovacao.

  3. SEM REDE. Mesma logica, pelo caminho de producao: `pega` levantando URLError.

  4. API RESPONDENDO success:false. Erro de autorizacao nao e interruptor
     desligado.

E o falso NEGATIVO que importa, que e o inverso e igualmente fatal:

  5. CANONICO AUSENTE tem de sair 2, nunca 0. Passar verde sem ter o que comparar
     e "gate verde sobre mundo vazio" -- exatamente o defeito que
     tools/check-edge-rule-drift foi escrito para nao repetir.

  6. ENDPOINT DO SELETOR. Medido em 2026-08-28: o caminho `/settings/
     tiered_cache_smart_topology_enable` devolve HTTP 400 code 1003 "Undefined
     zone setting"; o real e `/cache/...`. O teste trava isso no arquivo canonico
     porque um gate apontado para o caminho errado recebe 400, trata como
     indisponibilidade e passa verde PARA SEMPRE.

Rodar:
    python3 tools/test_check_edge_tiered_drift.py
    python3 -m unittest discover -s tools -p 'test_check_edge_tiered_drift.py'
"""

from __future__ import annotations

import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
import urllib.error

RAIZ = pathlib.Path(__file__).resolve().parent.parent
GATE = RAIZ / "tools" / "check-edge-tiered-drift"
CANONICO = RAIZ / "ops" / "cloudflare" / "tiered-cache.json"

MESTRE = "tiered_caching"
SELETOR = "tiered_cache_smart_topology_enable"


def envelope(valor, modified_on="2026-08-24T22:36:17.557113Z", editable=False):
    """O corpo que a API devolve. O fixture usa a MESMA estrutura da resposta real
    para que fixture e producao atravessem o mesmo parser."""
    return {"result": {"id": "x", "value": valor, "modified_on": modified_on,
                       "editable": editable},
            "success": True, "errors": [], "messages": []}


def roda(fixture=None, wiki_root=None, com_credencial=False, json_flag=True):
    """Executa o gate em subprocesso. Devolve (returncode, stdout, relatorio)."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLOUDFLARE_")}
    # Sem isto, importar a ferramenta sem extensao deixa .pyc em tools/__pycache__.
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["WIKI_ROOT"] = str(wiki_root or RAIZ)
    env.pop("WIKI_TIERED_FIXTURE", None)
    if com_credencial:
        env["CLOUDFLARE_ZONE_TOKEN"] = "token-de-teste-nunca-usado-em-rede"
    tmp = None
    if fixture is not None:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        json.dump(fixture, tmp)
        tmp.close()
        env["WIKI_TIERED_FIXTURE"] = tmp.name
    try:
        cmd = [sys.executable, str(GATE)] + (["--json"] if json_flag else [])
        p = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=120)
    finally:
        if tmp is not None:
            os.unlink(tmp.name)
    relatorio = None
    if json_flag and p.stdout.strip():
        relatorio = json.loads(p.stdout)
    return p.returncode, p.stdout + p.stderr, relatorio


def raiz_sem_credencial():
    """Arvore temporaria COM o canonico e SEM .env.local. Copiar o canonico e
    essencial: sem ele o gate sairia 2 (harness quebrado) e o teste de credencial
    nao chegaria a exercitar o caminho que pretende testar."""
    d = tempfile.mkdtemp(prefix="tiered-sem-cred-")
    destino = pathlib.Path(d) / "ops" / "cloudflare"
    destino.mkdir(parents=True)
    shutil.copy(CANONICO, destino / "tiered-cache.json")
    return d


def carrega_gate():
    """Importa a ferramenta como modulo (ela nao tem extensao .py). Seguro: todo o
    trabalho dela esta atras de `if __name__ == '__main__'`."""
    loader = importlib.machinery.SourceFileLoader("gate_tiered_drift", str(GATE))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


class EstadoBom(unittest.TestCase):
    def test_dois_ligados_passa(self):
        rc, saida, rel = roda({MESTRE: envelope("on"), SELETOR: envelope("on", editable=True)})
        self.assertEqual(rc, 0, saida)
        self.assertTrue(rel["verificada"], saida)
        self.assertFalse(rel["drift"], saida)
        self.assertEqual(len(rel["interruptores"]), 2, saida)

    def test_falso_positivo_metadado_que_muda_sozinho(self):
        """O estado REAL de producao: o mestre responde editable:false e continua
        valendo. Somado a um modified_on de outro dia, nada disso e drift.

        Se este teste passar a REPROVAR, o gate comecou a comparar metadado e vai
        gritar falso a cada mexida de painel."""
        rc, saida, rel = roda({
            MESTRE: envelope("on", modified_on="2027-01-01T00:00:00Z", editable=False),
            SELETOR: envelope("on", modified_on="2027-01-01T00:00:00Z", editable=True),
        })
        self.assertEqual(rc, 0, saida)
        self.assertTrue(rel["verificada"], saida)
        self.assertFalse(rel["drift"], saida)
        # E o metadado tem de continuar VISIVEL: e ele que data a derivacao.
        self.assertEqual(rel["interruptores"][0]["modified_on"], "2027-01-01T00:00:00Z", saida)


class Drift(unittest.TestCase):
    def test_mestre_desligado_reprova_e_nomeia(self):
        rc, saida, rel = roda({MESTRE: envelope("off"), SELETOR: envelope("on", editable=True)})
        self.assertEqual(rc, 1, saida)
        self.assertTrue(rel["drift"], saida)
        self.assertIn(MESTRE, rel["motivo"])
        self.assertNotIn(SELETOR, rel["motivo"])
        # A mensagem tem de dizer O QUE ACONTECE se ficar assim, nao so 'divergiu'.
        consequencia = " ".join(c["consequencia"] for c in rel["consequencias"])
        self.assertIn("INERTE", consequencia)
        self.assertIn("530", consequencia)

    def test_mestre_desligado_mensagem_humana_tambem_explica(self):
        rc, saida, _ = roda({MESTRE: envelope("off"), SELETOR: envelope("on", editable=True)},
                            json_flag=False)
        self.assertEqual(rc, 1, saida)
        self.assertIn("FAIL", saida)
        self.assertIn(MESTRE, saida)
        self.assertIn("O que acontece se ficar assim", saida)
        self.assertIn("tunel", saida.lower())

    def test_seletor_desligado_reprova_e_nomeia(self):
        rc, saida, rel = roda({MESTRE: envelope("on"), SELETOR: envelope("off", editable=True)})
        self.assertEqual(rc, 1, saida)
        self.assertIn(SELETOR, rel["motivo"])
        consequencia = " ".join(c["consequencia"] for c in rel["consequencias"])
        self.assertIn("aquecimento", consequencia.lower())

    def test_os_dois_desligados_nomeia_os_dois(self):
        rc, saida, rel = roda({MESTRE: envelope("off"), SELETOR: envelope("off", editable=True)})
        self.assertEqual(rc, 1, saida)
        self.assertEqual(len(rel["consequencias"]), 2, saida)


class FalsosPositivos(unittest.TestCase):
    def test_sem_credencial_nao_reprova(self):
        raiz = raiz_sem_credencial()
        try:
            rc, saida, rel = roda(wiki_root=raiz, com_credencial=False)
        finally:
            shutil.rmtree(raiz, ignore_errors=True)
        self.assertEqual(rc, 0, saida)
        # As duas asserçoes juntas: exit 0 sozinho seria indistinguivel de aprovacao.
        self.assertFalse(rel["verificada"], saida)
        self.assertFalse(rel["drift"], saida)
        self.assertIn("credencial", rel["motivo"])

    def test_sem_credencial_texto_nao_se_declara_aprovado(self):
        raiz = raiz_sem_credencial()
        try:
            rc, saida, _ = roda(wiki_root=raiz, com_credencial=False, json_flag=False)
        finally:
            shutil.rmtree(raiz, ignore_errors=True)
        self.assertEqual(rc, 0, saida)
        self.assertIn("NAO VERIFICADA", saida)
        self.assertNotIn("OK (", saida)

    def test_api_sem_sucesso_nao_e_drift(self):
        """403/authz devolve success:false. Isso e indisponibilidade, nao
        interruptor desligado."""
        ruim = {"result": None, "success": False,
                "errors": [{"code": 10000, "message": "Authentication error"}]}
        rc, saida, rel = roda({MESTRE: ruim, SELETOR: ruim})
        self.assertEqual(rc, 0, saida)
        self.assertFalse(rel["verificada"], saida)
        self.assertFalse(rel["drift"], saida)
        self.assertIn("Authentication error", rel["motivo"])

    def test_sem_rede_nao_reprova(self):
        """Exercita o caminho de PRODUCAO (urlopen), nao o de fixture: substitui
        `pega` por uma que levanta URLError, como faria uma maquina sem rota."""
        gate = carrega_gate()
        original = gate._irmao

        class IrmaoFalso:
            @staticmethod
            def ambiente():
                return {"CLOUDFLARE_ZONE_TOKEN": "token-de-teste"}

            @staticmethod
            def _credenciais(env, precisa_escrever=False):
                return ({"Authorization": "Bearer token-de-teste"}, "zone-token")

            @staticmethod
            def pega(url, cabecalhos):
                raise urllib.error.URLError("Network is unreachable")

        gate._irmao = lambda: IrmaoFalso
        argv = sys.argv
        buffer = io.StringIO()
        try:
            sys.argv = ["check-edge-tiered-drift", "--json"]
            os.environ.pop("WIKI_TIERED_FIXTURE", None)
            with contextlib.redirect_stdout(buffer):
                rc = gate.main()
        finally:
            gate._irmao = original
            sys.argv = argv
        rel = json.loads(buffer.getvalue())
        self.assertEqual(rc, 0, buffer.getvalue())
        self.assertFalse(rel["verificada"])
        self.assertFalse(rel["drift"])
        self.assertIn("Network is unreachable", rel["motivo"])


class HarnessQuebrado(unittest.TestCase):
    def test_canonico_ausente_sai_2_e_nao_0(self):
        """Sem canonico nao ha o que comparar. Exit 0 aqui seria afirmar 'nao ha
        drift' sem ter olhado -- gate verde sobre mundo vazio."""
        vazio = tempfile.mkdtemp(prefix="tiered-sem-canonico-")
        try:
            rc, saida, rel = roda(fixture={MESTRE: envelope("on")}, wiki_root=vazio)
        finally:
            shutil.rmtree(vazio, ignore_errors=True)
        self.assertEqual(rc, 2, saida)
        self.assertFalse(rel["verificada"], saida)

    def test_fixture_ilegivel_sai_2(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("CLOUDFLARE_")}
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["WIKI_ROOT"] = str(RAIZ)
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        tmp.write("{isto nao e json")
        tmp.close()
        env["WIKI_TIERED_FIXTURE"] = tmp.name
        try:
            p = subprocess.run([sys.executable, str(GATE), "--json"],
                               capture_output=True, text=True, env=env, timeout=120)
        finally:
            os.unlink(tmp.name)
        self.assertEqual(p.returncode, 2, p.stdout + p.stderr)


class Canonico(unittest.TestCase):
    def test_declara_os_dois_interruptores_com_consequencia(self):
        dados = json.loads(CANONICO.read_text(encoding="utf-8"))
        ids = [i["id"] for i in dados["interruptores"]]
        self.assertEqual(sorted(ids), sorted([MESTRE, SELETOR]))
        for i in dados["interruptores"]:
            self.assertEqual(i["valor_esperado"], "on")
            # Sem consequencia escrita, a mensagem de FAIL nao consegue dizer o
            # que acontece -- e o gate vira um numero sem significado.
            self.assertTrue(i.get("consequencia_se_off"), i["id"])
            self.assertTrue(i.get("papel"), i["id"])

    def test_endpoint_do_seletor_e_cache_e_nao_settings(self):
        """Medido em 2026-08-28: /zones/{z}/settings/tiered_cache_smart_topology_enable
        devolve HTTP 400 code 1003 'Undefined zone setting'. O caminho real e
        /zones/{z}/cache/... . Se alguem 'corrigir' isto para /settings/, o gate
        passa a receber 400, trata como indisponibilidade e fica verde para sempre."""
        dados = json.loads(CANONICO.read_text(encoding="utf-8"))
        seletor = [i for i in dados["interruptores"] if i["id"] == SELETOR][0]
        self.assertIn("/cache/", seletor["endpoint"])
        self.assertNotIn("/settings/", seletor["endpoint"])
        mestre = [i for i in dados["interruptores"] if i["id"] == MESTRE][0]
        self.assertIn("/argo/", mestre["endpoint"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
