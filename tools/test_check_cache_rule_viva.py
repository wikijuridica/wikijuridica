#!/usr/bin/env python3
"""Testes de tools/check-cache-rule-viva — a Cache Rule da zona esta viva e e a versionada?

TODO teste roda OFFLINE. O gate le a zona por GET em producao; aqui ele le um
fixture por --ruleset-json, que atravessa o MESMO parser (`extrai_ruleset` ->
`avalia`). Teste que dependesse de rede viraria teste que ninguem roda, e o
defeito que o gate existe para pegar reapareceria dentro da suite.

O PESO ESTA NO CASO RUIM REPROVANDO. Gate verde nao e prova; o que prova e a
reprovacao no estado que de fato aconteceu:

  1. ZERO REGRAS -- o ruleset v14 de 2026-08-22T13:10Z a 2026-08-26T15:55Z,
     tal como o ledger data/ops/edge_rule_apply.jsonl o guarda (`regras_antes:
     []`). Exit 1, e a mensagem diz ZERO.
  2. CHAVE `rules` AUSENTE e o mesmo estado (a API omite lista vazia em outros
     endpoints; este gate nao pode depender de qual forma vem). Exit 1, nunca 2.
  3. CAMPO QUE DECIDE COMPORTAMENTO divergindo: edge_ttl trocado por override,
     vary.headers.accept removido, regra desligada. Exit 1, e a divergencia
     NOMEIA o campo.
  4. REGRA A MAIS no ar (template de painel, como v9-v11 de agosto). Exit 1.

E os "NAO RODOU", que tem de sair 2 e nunca 0 -- exit 0 sem ter lido a zona e
o buraco de agosto por outra porta:

  5. Sem credencial (WIKI_ROOT sem .env.local e CLOUDFLARE_* limpos do ambiente).
  6. API success:false.
  7. Canonico ausente.
  8. Fixture ilegivel.

E o falso positivo coberto: 9. o corpo versionado, embrulhado no envelope da API
com os metadados que a API acrescenta (id, ref, version, last_updated,
description reescrita), tem de PASSAR -- metadado nunca reprova.

10. GET-ONLY por construcao: o fonte do gate nao contem PUT/PATCH/DELETE nem
    passa `metodo=` a `chamar`. Um gate que escreve na zona nao e gate.

Rodar:
    python3 tools/test_check_cache_rule_viva.py
"""
from __future__ import annotations

import copy
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
GATE = RAIZ / "tools" / "check-cache-rule-viva"
CANONICO = RAIZ / "ops" / "cloudflare" / "cache-rules.json"
FASE = "http_request_cache_settings"


def regras_canonicas():
    with open(CANONICO, encoding="utf-8") as f:
        return json.load(f)["rules"]


def envelope(rules, version="15", incluir_chave_rules=True):
    """O corpo que a API devolve para /rulesets/phases/<fase>/entrypoint, com os
    metadados reais que ela acrescenta em cada regra."""
    vivas = []
    for i, r in enumerate(rules):
        v = copy.deepcopy(r)
        v.update({"id": f"{i:032x}", "ref": f"{i:032x}", "version": "1",
                  "last_updated": "2026-08-26T15:55:35.269157Z",
                  "description": "descricao reescrita no painel, que nao decide nada"})
        vivas.append(v)
    resultado = {"id": "r", "name": "wikijuridica — cache de HTML na borda", "phase": FASE,
                 "version": version, "last_updated": "2026-08-26T15:55:35.269157Z"}
    if incluir_chave_rules:
        resultado["rules"] = vivas
    return {"success": True, "errors": [], "messages": [], "result": resultado}


class Bancada(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="cache-rule-viva-")

    def tearDown(self):
        for nome in os.listdir(self.tmp):
            os.unlink(os.path.join(self.tmp, nome))
        os.rmdir(self.tmp)

    def fixture(self, corpo, nome="ruleset.json", bruto=None):
        caminho = os.path.join(self.tmp, nome)
        with open(caminho, "w", encoding="utf-8") as f:
            if bruto is not None:
                f.write(bruto)
            else:
                json.dump(corpo, f, ensure_ascii=False)
        return caminho

    def roda(self, *args, env_extra=None, limpar_credencial=False):
        env = {k: v for k, v in os.environ.items()
               if not (limpar_credencial and k.startswith("CLOUDFLARE_"))}
        env.update(env_extra or {})
        p = subprocess.run([sys.executable, str(GATE), *args], capture_output=True,
                           text=True, env=env, timeout=60)
        return p.returncode, p.stdout + p.stderr

    # --- caso ruim reprovando -------------------------------------------------

    def test_1_zero_regras_reprova(self):
        f = self.fixture(envelope([], version="14"))
        codigo, saida = self.roda("--ruleset-json", f)
        self.assertEqual(codigo, 1, saida)
        self.assertIn("ZERO regras", saida)
        self.assertIn("FAIL", saida)

    def test_2_chave_rules_ausente_e_zero_regras(self):
        f = self.fixture(envelope([], version="14", incluir_chave_rules=False))
        codigo, saida = self.roda("--ruleset-json", f)
        self.assertEqual(codigo, 1, saida)
        self.assertIn("ZERO regras", saida)

    def test_3a_edge_ttl_divergente_reprova_e_nomeia_o_campo(self):
        regras = regras_canonicas()
        regras[0]["action_parameters"]["edge_ttl"] = {"mode": "override_origin", "default": 3600}
        f = self.fixture(envelope(regras))
        codigo, saida = self.roda("--ruleset-json", f)
        self.assertEqual(codigo, 1, saida)
        self.assertIn("regra 0 edge_ttl:", saida)
        self.assertNotIn("regra 0 browser_ttl:", saida)

    def test_3b_vary_accept_ausente_reprova(self):
        regras = regras_canonicas()
        del regras[0]["action_parameters"]["vary"]
        f = self.fixture(envelope(regras))
        codigo, saida = self.roda("--ruleset-json", f)
        self.assertEqual(codigo, 1, saida)
        self.assertIn("regra 0 vary.headers.accept:", saida)

    def test_3c_browser_ttl_divergente_reprova(self):
        regras = regras_canonicas()
        regras[0]["action_parameters"]["browser_ttl"] = {"mode": "override_origin", "default": 14400}
        f = self.fixture(envelope(regras))
        codigo, saida = self.roda("--ruleset-json", f)
        self.assertEqual(codigo, 1, saida)
        self.assertIn("regra 0 browser_ttl:", saida)

    def test_3d_regra_desligada_reprova(self):
        regras = regras_canonicas()
        regras[0]["enabled"] = False
        f = self.fixture(envelope(regras))
        codigo, saida = self.roda("--ruleset-json", f)
        self.assertEqual(codigo, 1, saida)
        self.assertIn("regra 0 enabled:", saida)

    def test_4_regra_a_mais_no_ar_reprova(self):
        # A CONTAGEM SAI DO DADO, NAO DE UM NUMERO ESCRITO AQUI (2026-09-05).
        # A fixture e montada A PARTIR de ops/cloudflare/cache-rules.json, entao
        # o "contra N versionada(s)" e propriedade do arquivo real. Com o numero
        # fixo, o dia em que a frente da borda versionou a segunda regra este
        # teste passou a reprovar sozinho — medido na primeira passada da suite
        # diaria: esperava "2 no ar contra 1", o gate disse "3 contra 2". Nao
        # havia defeito nenhum no detector; o teste e que tinha decorado o
        # tamanho do dado de ontem.
        regras = regras_canonicas()
        template = {"action": "set_cache_settings", "expression": "true", "enabled": True,
                    "action_parameters": {"cache": True, "edge_ttl": {"mode": "override_origin", "default": 7200}}}
        f = self.fixture(envelope(regras + [template]))
        codigo, saida = self.roda("--ruleset-json", f)
        self.assertEqual(codigo, 1, saida)
        self.assertIn("%d regra(s) no ar contra %d versionada(s)"
                      % (len(regras) + 1, len(regras)), saida)

    # --- NAO RODOU: exit 2, nunca 0 ---------------------------------------------

    def test_5_sem_credencial_nao_rodou(self):
        raiz_vazia = os.path.join(self.tmp, "raiz")
        os.mkdir(raiz_vazia)
        try:
            codigo, saida = self.roda("--canonico", str(CANONICO),
                                      env_extra={"WIKI_ROOT": raiz_vazia}, limpar_credencial=True)
        finally:
            os.rmdir(raiz_vazia)
        self.assertEqual(codigo, 2, saida)
        self.assertIn("NAO RODOU", saida)
        self.assertNotIn(": OK", saida)

    def test_6_api_success_false_nao_rodou(self):
        f = self.fixture({"success": False, "errors": [{"code": 10000, "message": "Authentication error"}],
                          "result": None})
        codigo, saida = self.roda("--ruleset-json", f)
        self.assertEqual(codigo, 2, saida)
        self.assertIn("NAO RODOU", saida)

    def test_7_canonico_ausente_nao_rodou(self):
        f = self.fixture(envelope(regras_canonicas()))
        codigo, saida = self.roda("--ruleset-json", f, "--canonico", os.path.join(self.tmp, "nao-existe.json"))
        self.assertEqual(codigo, 2, saida)
        self.assertIn("NAO RODOU", saida)

    def test_8_fixture_ilegivel_nao_rodou(self):
        f = self.fixture(None, nome="quebrado.json", bruto="{\"success\": true, ")
        codigo, saida = self.roda("--ruleset-json", f)
        self.assertEqual(codigo, 2, saida)
        self.assertIn("NAO RODOU", saida)

    # --- falso positivo coberto -------------------------------------------------

    def test_9_versionado_com_metadado_da_api_passa(self):
        f = self.fixture(envelope(regras_canonicas()))
        codigo, saida = self.roda("--ruleset-json", f)
        self.assertEqual(codigo, 0, saida)
        self.assertIn(": OK", saida)
        codigo, saida = self.roda("--ruleset-json", f, "--json")
        self.assertEqual(codigo, 0, saida)
        relatorio = json.loads(saida)
        self.assertEqual(relatorio["divergencias"], [])
        # Mesmo motivo do test_4: a fixture E o canonico, entao o numero de
        # regras vivas so pode vir do canonico. Preso em 1, este assert quebrou
        # no dia em que a segunda regra foi versionada.
        self.assertEqual(relatorio["regras_vivas"], len(regras_canonicas()))

    # --- GET-ONLY por construcao ------------------------------------------------

    def test_10_gate_nao_escreve_na_zona(self):
        fonte = GATE.read_text(encoding="utf-8")
        corpo = fonte.split('"""', 2)[2]  # fora do docstring
        for proibido in ('"PUT"', '"PATCH"', '"DELETE"', '"POST"', "metodo=", "method="):
            self.assertNotIn(proibido, corpo, f"{proibido} apareceu no gate read-only")
        self.assertIn("_credenciais(env, precisa_escrever=False)", corpo)


if __name__ == "__main__":
    unittest.main(verbosity=1)
