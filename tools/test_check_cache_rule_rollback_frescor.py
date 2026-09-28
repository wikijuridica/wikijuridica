#!/usr/bin/env python3
"""Testes de tools/check-cache-rule-rollback-frescor e tools/generate-cache-rule-rollback.

TODO teste aqui roda OFFLINE. Nenhum abre socket, e isso e requisito, nao
conveniencia: o defeito que este gate existe para nao cometer -- ler
indisponibilidade de API como veredito -- reapareceria dentro da propria suite se
o teste dependesse da rede.

O PESO ESTA NOS FALSOS POSITIVOS. Este repositorio ja teve detector que acusou 46
paginas sendo que as 46 eram falso positivo, e o gate irmao
tools/check-edge-tiered-drift documenta a mesma licao por outro caminho: metadado
que muda sozinho faz o gate gritar ate o operador aprender a ignora-lo.

Os casos inocentes cobertos aqui, cada um com o comportamento errado que reprova:

  1. SEM CREDENCIAL. Maquina sem .env.local nao tem snapshot velho, tem falta de
     instrumento. Exige exit 2.
  2. API FORA (URLError) e 3. API COM success:false. Mesma logica pelo caminho de
     producao: o snapshot nao ficou pior porque a Cloudflare oscilou.
  4. ZONA COM ZERO REGRAS. Aconteceu de verdade em 2026-08-22 (ruleset v14,
     cobertura de cache 0,0%). Comparar o snapshot com o vazio o reprovaria pelo
     motivo errado -- o culpado e a zona, e quem a julga e check-edge-rule-drift.
  5. RUIDO DE METADADO. Snapshot semanticamente igual ao vivo, mas com `id`,
     `version`, `ref`, `last_updated` presentes nas regras e `description`
     reescrita. Um gate que comparasse o objeto cru reprovaria isso todo dia.
  6. CARIMBO DEFASADO COM CONTEUDO IDENTICO. Version do ruleset sobe por qualquer
     edicao da fase, inclusive por um PUT que reponha o MESMO corpo depois de um
     apagao de painel. Restaurar a foto ali e inocuo, e reprovar seria acusar
     quem esta apagando incendio. Exige exit 0 -- com o aviso nomeado na saida,
     porque exit 0 mudo seria indistinguivel de aprovacao plena.

E os verdadeiros positivos, que sem eles o gate seria so um exit 0 caro:

  7. O SNAPSHOT REAL DE 2026-08-12, congelado, contra a regra viva de 2026-08-26.
     Exige exit 1 e exige que o diff NOMEIE `vary` e `edge_ttl` -- reprovar sem
     dizer o campo obriga o operador a diffar na mao no pior momento possivel.
  8. NUMERO DE REGRAS DIFERENTE.
  9. ROUND-TRIP: o que o gerador monta tem de passar no gate. Gerador e gate
     discordando sobre o formato e o bug classico de par gerador/validador.
"""
import importlib.machinery
import importlib.util
import json
import os
import tempfile
import unittest
import urllib.error

TOOLS = os.path.dirname(os.path.abspath(__file__))


def _carregar(nome, alias):
    caminho = os.path.join(TOOLS, nome)
    loader = importlib.machinery.SourceFileLoader(alias, caminho)
    spec = importlib.util.spec_from_loader(alias, loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


GATE = _carregar("check-cache-rule-rollback-frescor", "gate_frescor")
GERADOR = _carregar("generate-cache-rule-rollback", "gerador_rollback")
NORMALIZA = GATE.irmao().normaliza

EXPRESSAO_VIVA = (
    '(http.host eq "wikijuridica.com.br" or http.host eq "www.wikijuridica.com.br") '
    'and not starts_with(http.request.uri.path, "/buscar/") '
    'and not starts_with(http.request.uri.path, "/mcp")'
)
EXPRESSAO_2026_08_12 = (
    '(http.host eq "wikijuridica.com.br" or http.host eq "www.wikijuridica.com.br") '
    'and not starts_with(http.request.uri.path, "/buscar/")'
)

# Estado VIVO, reduzido ao que decide comportamento. `vary` e `respect_origin`
# sao os dois campos que a correcao de 2026-08-26 (be4a6cf4) introduziu.
REGRA_VIVA = {
    "action": "set_cache_settings",
    "action_parameters": {
        "browser_ttl": {"mode": "respect_origin"},
        "cache": True,
        "edge_ttl": {"mode": "respect_origin"},
        "origin_error_page_passthru": False,
        "vary": {"default": {"action": "normalize"},
                 "headers": {"accept": {"action": "normalize",
                                        "media_types": ["text/markdown"]}}},
    },
    "description": "Acervo cacheavel na borda com TTL por classe",
    "enabled": True,
    "expression": EXPRESSAO_VIVA,
    "id": "18a36363bee94c608e3376d9198cba8e",
    "last_updated": "2026-08-26T15:55:35.269157Z",
    "ref": "18a36363bee94c608e3376d9198cba8e",
    "version": "1",
}

# O ARQUIVO REAL que estava no disco, congelado em 2026-08-12T17:30.
REGRA_2026_08_12 = {
    "action": "set_cache_settings",
    "action_parameters": {
        "browser_ttl": {"mode": "respect_origin"},
        "cache": True,
        "edge_ttl": {"default": 604800, "mode": "override_origin"},
        "origin_error_page_passthru": False,
    },
    "description": "Acervo estatico cacheavel; exclui as rotas de corpo variavel e as de saude",
    "expression": EXPRESSAO_2026_08_12,
}


def vivo(regras=None, versao="15"):
    return {
        "id": "4bd6a5aa90014e798d3b230c878268db",
        "name": "wikijuridica — cache de HTML na borda",
        "version": versao,
        "last_updated": "2026-08-26T15:55:35.269157Z",
        "rules": [json.loads(json.dumps(REGRA_VIVA))] if regras is None else regras,
    }


class IrmaoFalso:
    """Dubie da leitura de credencial/HTTP de check-edge-rule-drift."""

    def __init__(self, cabecalhos=("h",), resposta=None, excecao=None):
        self._cabecalhos = {"Authorization": "Bearer x"} if cabecalhos else None
        self._resposta = resposta
        self._excecao = excecao
        self.normaliza = NORMALIZA

    def ambiente(self):
        return {}

    def _credenciais(self, env, precisa_escrever=False):
        return (self._cabecalhos, "zone-token" if self._cabecalhos else "sem-credencial")

    def pega(self, url, cabecalhos):
        if self._excecao:
            raise self._excecao
        return self._resposta


class FalsosPositivos(unittest.TestCase):
    def test_1_sem_credencial_nao_e_snapshot_velho(self):
        _, erro = GATE.ler_vivo(IrmaoFalso(cabecalhos=None))
        self.assertIsNotNone(erro)
        self.assertIn("sem credencial", erro)

    def test_2_api_fora_nao_e_snapshot_velho(self):
        _, erro = GATE.ler_vivo(IrmaoFalso(excecao=urllib.error.URLError("rede fora")))
        self.assertIsNotNone(erro)
        self.assertIn("nao alcancei", erro)

    def test_3_api_sem_sucesso_nao_e_snapshot_velho(self):
        _, erro = GATE.ler_vivo(IrmaoFalso(resposta={"success": False, "errors": [{"code": 10000}]}))
        self.assertIsNotNone(erro)
        self.assertIn("sem sucesso", erro)

    def test_3b_http_error_nao_e_snapshot_velho(self):
        erro_http = urllib.error.HTTPError("u", 403, "Forbidden", {}, None)
        _, erro = GATE.ler_vivo(IrmaoFalso(excecao=erro_http))
        self.assertIn("403", erro)

    def test_4_zona_vazia_sai_2_e_nao_1(self):
        codigo, linhas = GATE.avaliar({"rules": [REGRA_2026_08_12]}, vivo(regras=[]), NORMALIZA)
        self.assertEqual(codigo, 2, "\n".join(linhas))
        self.assertIn("ZERO regras", "\n".join(linhas))

    def test_5_ruido_de_metadado_nao_reprova(self):
        """Snapshot com id/version/ref/last_updated e description reescrita, mesma
        semantica: nada mudaria se fosse restaurado, entao verde."""
        regra = json.loads(json.dumps(REGRA_VIVA))
        regra["description"] = "outro texto humano, mesma regra"
        regra["version"] = "99"
        regra["last_updated"] = "2026-01-01T00:00:00Z"
        snap = {"_captura": {"capturado_em": "2026-08-28T00:00:00Z", "ruleset_version": "15"},
                "rules": [regra]}
        codigo, linhas = GATE.avaliar(snap, vivo(), NORMALIZA)
        self.assertEqual(codigo, 0, "\n".join(linhas))

    def test_6_carimbo_defasado_com_conteudo_identico_avisa_mas_nao_reprova(self):
        snap = {"_captura": {"capturado_em": "2026-08-20T00:00:00Z", "ruleset_version": "9"},
                "rules": [GATE.limpar_regra(REGRA_VIVA)]}
        codigo, linhas = GATE.avaliar(snap, vivo(versao="15"), NORMALIZA)
        texto = "\n".join(linhas)
        self.assertEqual(codigo, 0, texto)
        self.assertIn("AVISO", texto)
        self.assertIn("carimbo defasado", texto)

    def test_6b_sem_carimbo_com_conteudo_identico_avisa_mas_nao_reprova(self):
        snap = {"rules": [GATE.limpar_regra(REGRA_VIVA)]}
        codigo, linhas = GATE.avaliar(snap, vivo(), NORMALIZA)
        self.assertEqual(codigo, 0, "\n".join(linhas))
        self.assertIn("nao tem data", "\n".join(linhas))

    def test_snapshot_ausente_sai_2(self):
        dados, erro = GATE.ler_snapshot(os.path.join(tempfile.gettempdir(), "nao-existe-4f3a.json"))
        self.assertIsNone(dados)
        self.assertIn("ausente", erro)
        self.assertEqual(GATE.avaliar(None, vivo(), NORMALIZA)[0], 2)

    def test_snapshot_invalido_sai_2(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write("{isto nao e json")
            caminho = f.name
        try:
            dados, erro = GATE.ler_snapshot(caminho)
            self.assertIsNone(dados)
            self.assertIn("ilegivel", erro)
        finally:
            os.unlink(caminho)

    def test_snapshot_sem_array_rules_sai_2(self):
        codigo, linhas = GATE.avaliar({"_captura": {}}, vivo(), NORMALIZA)
        self.assertEqual(codigo, 2, "\n".join(linhas))


class VerdadeirosPositivos(unittest.TestCase):
    def test_7_snapshot_de_12_de_agosto_reprova_e_nomeia_os_campos(self):
        codigo, linhas = GATE.avaliar({"rules": [REGRA_2026_08_12]}, vivo(), NORMALIZA)
        texto = "\n".join(linhas)
        self.assertEqual(codigo, 1, texto)
        self.assertIn("action_parameters.vary", texto)
        self.assertIn("action_parameters.edge_ttl", texto)
        # A clausula de /mcp e o terceiro estrago, e o diff por clausula existe
        # porque as duas expressoes tem 600+ caracteres de prefixo identico.
        self.assertIn("/mcp", texto)

    def test_8_numero_de_regras_diferente_reprova(self):
        snap = {"rules": [GATE.limpar_regra(REGRA_VIVA), GATE.limpar_regra(REGRA_VIVA)]}
        codigo, linhas = GATE.avaliar(snap, vivo(), NORMALIZA)
        self.assertEqual(codigo, 1)
        self.assertIn("numero de regras", "\n".join(linhas))

    def test_regra_desabilitada_no_snapshot_reprova(self):
        regra = GATE.limpar_regra(REGRA_VIVA)
        regra["enabled"] = False
        codigo, linhas = GATE.avaliar({"rules": [regra]}, vivo(), NORMALIZA)
        self.assertEqual(codigo, 1)
        self.assertIn("enabled", "\n".join(linhas))


class ContratoDoGerador(unittest.TestCase):
    def test_limpar_regra_descarta_so_o_que_a_api_regenera(self):
        limpa = GATE.limpar_regra(REGRA_VIVA)
        for volatil in ("id", "version", "ref", "last_updated"):
            self.assertNotIn(volatil, limpa)
        self.assertEqual(limpa["expression"], EXPRESSAO_VIVA)
        self.assertIn("description", limpa, "description e texto util a quem le o rollback as pressas")

    def test_9_round_trip_o_que_o_gerador_monta_passa_no_gate(self):
        montado = GERADOR.montar(vivo(), "b2e1", "zone-token", GATE)
        codigo, linhas = GATE.avaliar(montado, vivo(), NORMALIZA)
        self.assertEqual(codigo, 0, "\n".join(linhas))
        self.assertNotIn("AVISO", "\n".join(linhas))

    def test_carimbo_traz_data_id_e_versao_legiveis(self):
        cap = GERADOR.montar(vivo(), "b2e1", "zone-token", GATE)["_captura"]
        self.assertTrue(cap["capturado_em"].endswith("Z"))
        self.assertEqual(cap["ruleset_id"], "4bd6a5aa90014e798d3b230c878268db")
        self.assertEqual(cap["ruleset_version"], "15")
        self.assertEqual(cap["ruleset_last_updated"], "2026-08-26T15:55:35.269157Z")

    def test_corpo_para_put_leva_so_rules(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(GERADOR.montar(vivo(), "b2e1", "zone-token", GATE), f)
            caminho = f.name
        try:
            corpo = GERADOR.corpo_para_put(caminho)
            self.assertEqual(list(corpo.keys()), ["rules"])
            self.assertNotIn("_captura", corpo)
        finally:
            os.unlink(caminho)

    def test_corpo_para_put_recusa_snapshot_sem_regras(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"_captura": {}, "rules": []}, f)
            caminho = f.name
        try:
            with self.assertRaises(ValueError):
                GERADOR.corpo_para_put(caminho)
        finally:
            os.unlink(caminho)


if __name__ == "__main__":
    unittest.main(verbosity=2)
