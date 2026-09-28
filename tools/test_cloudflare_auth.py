#!/usr/bin/env python3
"""Teste de tools/cloudflare_auth.py — sem rede, sem tocar `.env.local` real.

Cobre exatamente o que motivou o módulo (ver a docstring dele para a medição
completa): ordem de preferência por escopo, a proibição de
"Authorization: Bearer" com a Global API Key, a leitura de `.env.local` com
comentário/aspas/espaço, e que a ausência de uma das duas credenciais nunca
derruba o que a outra sozinha já alcança.

Nenhum teste aqui faz requisição de rede real nem lê o `.env.local` do
repositório: cada um usa um arquivo temporário próprio ou passa `env={...}`
direto, e `os.environ` é isolado de `CLOUDFLARE_*` em cada `setUp`.
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cloudflare_auth as ca  # noqa: E402  (tools/ nao e pacote; o caminho entra acima)


def _sem_cloudflare_no_ambiente():
    """Contexto que remove toda CLOUDFLARE_* do os.environ do processo de
    teste — nenhum teste deste arquivo pode depender (ou vazar) do
    .env.local real da máquina que o roda."""
    limpo = {k: v for k, v in os.environ.items() if not k.startswith("CLOUDFLARE_")}
    return mock.patch.dict(os.environ, limpo, clear=True)


class _BaseIsolada(unittest.TestCase):
    """Isola os.environ e limpa os caches em memória do módulo a cada teste,
    para um teste nunca ler o resultado cacheado de outro."""

    def setUp(self):
        self._ctx = _sem_cloudflare_no_ambiente()
        self._ctx.__enter__()
        # ENV_PADRAO aponta para um caminho que garantidamente nao existe --
        # nenhum teste deste arquivo pode ler o .env.local REAL da maquina que
        # o roda, nem por acidente via o caminho `env=None` (que cai em
        # ambiente() sem argumento).
        self._env_padrao_ctx = mock.patch.object(
            ca, "ENV_PADRAO",
            os.path.join(tempfile.gettempdir(), "cloudflare-auth-teste-inexistente.env"))
        self._env_padrao_ctx.start()
        ca._cache_verificar.clear()
        ca._cache_zona.clear()

    def tearDown(self):
        self._env_padrao_ctx.stop()
        self._ctx.__exit__(None, None, None)
        ca._cache_verificar.clear()
        ca._cache_zona.clear()

    def _escrever_env(self, conteudo):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False,
                                         encoding="utf-8")
        f.write(conteudo)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name


# --- ambiente(): leitura de .env.local -------------------------------------

class TestAmbiente(_BaseIsolada):
    def test_le_arquivo_simples(self):
        caminho = self._escrever_env("CLOUDFLARE_ZONE_TOKEN=abc123\n")
        env = ca.ambiente(caminho)
        self.assertEqual(env.get("CLOUDFLARE_ZONE_TOKEN"), "abc123")

    def test_ignora_comentario_e_linha_vazia(self):
        caminho = self._escrever_env(
            "# comentario no topo\n"
            "\n"
            "CLOUDFLARE_EMAIL=a@b.com\n"
            "   \n"
            "# outro comentario com = dentro dele\n"
            "CLOUDFLARE_API_TOKEN=xyz\n"
        )
        env = ca.ambiente(caminho)
        self.assertEqual(env.get("CLOUDFLARE_EMAIL"), "a@b.com")
        self.assertEqual(env.get("CLOUDFLARE_API_TOKEN"), "xyz")
        self.assertNotIn("comentario", env)
        self.assertNotIn("# comentario no topo", env.values())

    def test_aspas_simples_e_duplas_sao_removidas(self):
        caminho = self._escrever_env(
            'CLOUDFLARE_ZONE_TOKEN="com-aspas-duplas"\n'
            "CLOUDFLARE_EMAIL='com-aspas-simples'\n"
        )
        env = ca.ambiente(caminho)
        self.assertEqual(env.get("CLOUDFLARE_ZONE_TOKEN"), "com-aspas-duplas")
        self.assertEqual(env.get("CLOUDFLARE_EMAIL"), "com-aspas-simples")

    def test_espacos_ao_redor_da_chave_e_do_valor_sao_removidos(self):
        caminho = self._escrever_env("  CLOUDFLARE_ZONE_TOKEN =  espacado  \n")
        env = ca.ambiente(caminho)
        self.assertEqual(env.get("CLOUDFLARE_ZONE_TOKEN"), "espacado")

    def test_arquivo_ausente_nao_lanca_e_nao_traz_cloudflare(self):
        env = ca.ambiente("/caminho/definitivamente/inexistente/.env.local")
        self.assertEqual({k: v for k, v in env.items() if k.startswith("CLOUDFLARE_")}, {})

    def test_os_environ_tem_precedencia_sobre_o_arquivo(self):
        caminho = self._escrever_env("CLOUDFLARE_ZONE_TOKEN=do-arquivo\n")
        with mock.patch.dict(os.environ, {"CLOUDFLARE_ZONE_TOKEN": "do-ambiente"}):
            env = ca.ambiente(caminho)
        self.assertEqual(env.get("CLOUDFLARE_ZONE_TOKEN"), "do-ambiente")

    def test_variavel_nao_cloudflare_no_ambiente_nao_entra(self):
        caminho = self._escrever_env("CLOUDFLARE_ZONE_TOKEN=zt\n")
        with mock.patch.dict(os.environ, {"ALHEIA_QUALQUER": "1"}):
            env = ca.ambiente(caminho)
        self.assertNotIn("ALHEIA_QUALQUER", env)


# --- cabecalhos(): ordem de preferencia por escopo --------------------------

class TestCabecalhosOrdemDePreferencia(_BaseIsolada):
    def test_leitura_prefere_zone_token_quando_os_dois_existem(self):
        env = {"CLOUDFLARE_ZONE_TOKEN": "zt", "CLOUDFLARE_EMAIL": "a@b.com",
               "CLOUDFLARE_API_TOKEN": "gk"}
        cab, rotulo = ca.cabecalhos("leitura", env=env)
        self.assertEqual(rotulo, ca.ROTULO_ZONA)
        self.assertEqual(cab["Authorization"], "Bearer zt")

    def test_purga_prefere_zone_token_quando_os_dois_existem(self):
        env = {"CLOUDFLARE_ZONE_TOKEN": "zt", "CLOUDFLARE_EMAIL": "a@b.com",
               "CLOUDFLARE_API_TOKEN": "gk"}
        cab, rotulo = ca.cabecalhos("purga", env=env)
        self.assertEqual(rotulo, ca.ROTULO_ZONA)
        self.assertEqual(cab["Authorization"], "Bearer zt")

    def test_leitura_cai_para_global_key_sem_zone_token(self):
        env = {"CLOUDFLARE_EMAIL": "a@b.com", "CLOUDFLARE_API_TOKEN": "gk"}
        cab, rotulo = ca.cabecalhos("leitura", env=env)
        self.assertEqual(rotulo, ca.ROTULO_GLOBAL)
        self.assertEqual(cab["X-Auth-Email"], "a@b.com")
        self.assertEqual(cab["X-Auth-Key"], "gk")

    def test_escrita_ignora_zone_token_e_usa_global_key_direto(self):
        env = {"CLOUDFLARE_ZONE_TOKEN": "zt", "CLOUDFLARE_EMAIL": "a@b.com",
               "CLOUDFLARE_API_TOKEN": "gk"}
        cab, rotulo = ca.cabecalhos("escrita", env=env)
        self.assertEqual(rotulo, ca.ROTULO_GLOBAL)
        self.assertNotIn("Authorization", cab)

    def test_firewall_ignora_zone_token_e_usa_global_key_direto(self):
        env = {"CLOUDFLARE_ZONE_TOKEN": "zt", "CLOUDFLARE_EMAIL": "a@b.com",
               "CLOUDFLARE_API_TOKEN": "gk"}
        cab, rotulo = ca.cabecalhos("firewall", env=env)
        self.assertEqual(rotulo, ca.ROTULO_GLOBAL)
        self.assertNotIn("Authorization", cab)

    def test_escrita_sem_global_key_e_sem_credencial_mesmo_com_zone_token(self):
        """O token de zona NAO tem escopo de escrita (medido: PUT devolve
        403/10000). Cair para ele aqui seria uma chamada fadada -- o contrato
        e 'escrita' sem Global Key virar sem-credencial, nunca uma tentativa
        com Bearer de zona."""
        env = {"CLOUDFLARE_ZONE_TOKEN": "zt"}
        cab, rotulo = ca.cabecalhos("escrita", env=env)
        self.assertIsNone(cab)
        self.assertEqual(rotulo, ca.ROTULO_AUSENTE)

    def test_firewall_sem_global_key_e_sem_credencial_mesmo_com_zone_token(self):
        env = {"CLOUDFLARE_ZONE_TOKEN": "zt"}
        cab, rotulo = ca.cabecalhos("firewall", env=env)
        self.assertIsNone(cab)
        self.assertEqual(rotulo, ca.ROTULO_AUSENTE)

    def test_nada_de_credencial_e_sem_credencial_em_qualquer_escopo(self):
        for escopo in ("leitura", "purga", "escrita", "firewall"):
            with self.subTest(escopo=escopo):
                cab, rotulo = ca.cabecalhos(escopo, env={})
                self.assertIsNone(cab)
                self.assertEqual(rotulo, ca.ROTULO_AUSENTE)

    def test_escopo_invalido_lanca_valueerror(self):
        with self.assertRaises(ValueError):
            ca.cabecalhos("qualquer-coisa-que-nao-e-escopo", env={})

    def test_env_omitido_le_o_ambiente_do_processo(self):
        """Sem `env=`, cabecalhos() chama ambiente() sozinho -- que por sua
        vez le `ENV_PADRAO`. `_BaseIsolada.setUp` aponta `ENV_PADRAO` para um
        caminho garantidamente inexistente, entao o unico jeito de este teste
        achar uma credencial e via os.environ do processo, injetado abaixo --
        nunca o .env.local real da maquina."""
        with mock.patch.dict(os.environ, {"CLOUDFLARE_ZONE_TOKEN": "do-processo"}):
            cab, rotulo = ca.cabecalhos("leitura")
        self.assertEqual(rotulo, ca.ROTULO_ZONA)
        self.assertEqual(cab["Authorization"], "Bearer do-processo")


# --- a regra de ouro: nunca Bearer com a Global API Key ---------------------

class TestNuncaBearerComGlobalKey(_BaseIsolada):
    """O caso que 5 das 10 copias tratavam errado: CLOUDFLARE_API_TOKEN
    presente, sem CLOUDFLARE_EMAIL e sem CLOUDFLARE_ZONE_TOKEN. As copias
    faziam `Authorization: Bearer <api_token>` -- e essa combinacao devolve
    "Invalid API Token" da API real (medido, ver docstring do modulo). O
    contrato deste modulo e nunca tentar essa combinacao: sem-credencial
    (quem chama sai 2, "nao rodou") em vez de uma chamada fadada."""

    def test_api_token_sozinho_sem_email_e_sem_zone_token_e_sem_credencial(self):
        for escopo in ("leitura", "purga", "escrita", "firewall"):
            with self.subTest(escopo=escopo):
                cab, rotulo = ca.cabecalhos(escopo, env={"CLOUDFLARE_API_TOKEN": "gk-orfao"})
                self.assertIsNone(cab, f"escopo {escopo} nao deveria ter cabecalho")
                self.assertEqual(rotulo, ca.ROTULO_AUSENTE)

    def test_valor_do_api_token_nunca_aparece_atras_de_bearer(self):
        """Varre todos os escopos, com e sem e-mail/zone-token, e confere que
        o VALOR de CLOUDFLARE_API_TOKEN nunca vira 'Authorization: Bearer
        <esse valor>' em cabecalho nenhum devolvido."""
        api_token = "segredo-global-nao-e-bearer"
        combinacoes = (
            {"CLOUDFLARE_API_TOKEN": api_token},
            {"CLOUDFLARE_API_TOKEN": api_token, "CLOUDFLARE_EMAIL": "a@b.com"},
            {"CLOUDFLARE_API_TOKEN": api_token, "CLOUDFLARE_EMAIL": "a@b.com",
             "CLOUDFLARE_ZONE_TOKEN": "zt"},
            {"CLOUDFLARE_API_TOKEN": api_token, "CLOUDFLARE_ZONE_TOKEN": "zt"},
        )
        for env in combinacoes:
            for escopo in ("leitura", "purga", "escrita", "firewall"):
                cab, _ = ca.cabecalhos(escopo, env=env)
                if cab and "Authorization" in cab:
                    self.assertNotEqual(
                        cab["Authorization"], f"Bearer {api_token}",
                        f"escopo {escopo!r} env {env!r} usou Bearer com a Global Key")


# --- ausencia de uma credencial nao derruba o que a outra alcanca -----------

class TestAusenciaDeUmaCredencialNaoDerrubaAOutra(_BaseIsolada):
    def test_so_zone_token_ainda_alcanca_leitura_e_purga(self):
        env = {"CLOUDFLARE_ZONE_TOKEN": "zt"}
        for escopo in ("leitura", "purga"):
            with self.subTest(escopo=escopo):
                cab, rotulo = ca.cabecalhos(escopo, env=env)
                self.assertIsNotNone(cab, f"escopo {escopo} deveria funcionar so com zone token")
                self.assertEqual(rotulo, ca.ROTULO_ZONA)

    def test_so_global_key_ainda_alcanca_os_quatro_escopos(self):
        env = {"CLOUDFLARE_EMAIL": "a@b.com", "CLOUDFLARE_API_TOKEN": "gk"}
        for escopo in ("leitura", "purga", "escrita", "firewall"):
            with self.subTest(escopo=escopo):
                cab, rotulo = ca.cabecalhos(escopo, env=env)
                self.assertIsNotNone(cab, f"escopo {escopo} deveria funcionar so com global key")
                self.assertEqual(rotulo, ca.ROTULO_GLOBAL)

    def test_email_sem_api_token_nao_e_credencial_global_valida(self):
        """So metade do par (email sem token, ou token sem email) nao monta
        Global Key -- e sem zone token no ambiente, isso e sem-credencial."""
        cab, rotulo = ca.cabecalhos("leitura", env={"CLOUDFLARE_EMAIL": "a@b.com"})
        self.assertIsNone(cab)
        self.assertEqual(rotulo, ca.ROTULO_AUSENTE)

    def test_arquivo_sozinho_sem_residuo_no_os_environ_ainda_funciona(self):
        """os.environ limpo (setUp) nao apaga o que so o ARQUIVO declara."""
        caminho = self._escrever_env("CLOUDFLARE_ZONE_TOKEN=do-arquivo-sozinho\n")
        env = ca.ambiente(caminho)
        cab, rotulo = ca.cabecalhos("leitura", env=env)
        self.assertEqual(rotulo, ca.ROTULO_ZONA)
        self.assertEqual(cab["Authorization"], "Bearer do-arquivo-sozinho")


# --- pega/graphql/zona_id/verificar: sem rede quando sem credencial --------

class _RespostaFalsa:
    def __init__(self, corpo, status=200):
        self._corpo = corpo
        self.status = status

    def read(self):
        return json.dumps(self._corpo).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class TestPegaGraphqlSemCredencialNaoFazemRede(_BaseIsolada):
    def test_pega_sem_credencial_nao_chama_urlopen(self):
        with mock.patch("cloudflare_auth.urllib.request.urlopen") as m:
            dados, erro = ca.pega("https://api.cloudflare.com/client/v4/zones", "leitura", env={})
        m.assert_not_called()
        self.assertIsNone(dados)
        self.assertEqual(erro, ca.ROTULO_AUSENTE)

    def test_graphql_sem_credencial_nao_chama_urlopen(self):
        with mock.patch("cloudflare_auth.urllib.request.urlopen") as m:
            dados, erro = ca.graphql("query{}", {}, escopo="leitura", env={})
        m.assert_not_called()
        self.assertIsNone(dados)
        self.assertEqual(erro, ca.ROTULO_AUSENTE)

    def test_zona_id_sem_credencial_nao_chama_urlopen(self):
        with mock.patch("cloudflare_auth.urllib.request.urlopen") as m:
            zid, erro = ca.zona_id("exemplo.com.br", env={})
        m.assert_not_called()
        self.assertIsNone(zid)
        self.assertEqual(erro, ca.ROTULO_AUSENTE)

    def test_verificar_sem_credencial_nao_chama_urlopen(self):
        with mock.patch("cloudflare_auth.urllib.request.urlopen") as m:
            ok, detalhe = ca.verificar("firewall", env={"CLOUDFLARE_ZONE_TOKEN": "zt"})
        m.assert_not_called()
        self.assertFalse(ok)
        self.assertEqual(detalhe, ca.ROTULO_AUSENTE)


class TestZonaIdComCacheEVerificarEscolhemEndpointCerto(_BaseIsolada):
    def test_zona_id_usa_cache_na_segunda_chamada(self):
        env = {"CLOUDFLARE_ZONE_TOKEN": "zt"}
        with mock.patch("cloudflare_auth.urllib.request.urlopen",
                         return_value=_RespostaFalsa({"result": [{"id": "zid123"}]})) as m:
            zid1, erro1 = ca.zona_id("exemplo-cache.com.br", env=env)
            zid2, erro2 = ca.zona_id("exemplo-cache.com.br", env=env)
        self.assertEqual(zid1, "zid123")
        self.assertEqual(zid2, "zid123")
        self.assertIsNone(erro1)
        self.assertIsNone(erro2)
        self.assertEqual(m.call_count, 1,
                          "segunda chamada deveria vir do cache, sem nova requisicao")

    def test_zona_id_sem_resultado_nao_cacheia_e_reporta_erro(self):
        env = {"CLOUDFLARE_ZONE_TOKEN": "zt"}
        with mock.patch("cloudflare_auth.urllib.request.urlopen",
                         return_value=_RespostaFalsa({"result": []})):
            zid, erro = ca.zona_id("nao-existe.com.br", env=env)
        self.assertIsNone(zid)
        self.assertIn("nao-existe.com.br", erro)

    def test_zona_id_com_success_false_surge_a_mensagem_da_api(self):
        """A API recusando por escopo (success:false) tem de aparecer no erro
        -- cair no 'zona nao encontrada' genérico esconderia a causa real."""
        env = {"CLOUDFLARE_ZONE_TOKEN": "zt"}
        resposta = {"success": False,
                    "errors": [{"code": 10000, "message": "Authentication error"}],
                    "result": None}
        with mock.patch("cloudflare_auth.urllib.request.urlopen",
                         return_value=_RespostaFalsa(resposta)):
            zid, erro = ca.zona_id("exemplo-sem-escopo.com.br", env=env)
        self.assertIsNone(zid)
        self.assertIn("Authentication error", erro)

    def test_verificar_com_zone_token_bate_em_tokens_verify(self):
        urls = []

        def urlopen_falso(req, timeout=None):
            urls.append(req.full_url)
            return _RespostaFalsa({"success": True})

        with mock.patch("cloudflare_auth.urllib.request.urlopen", side_effect=urlopen_falso):
            ok, detalhe = ca.verificar("leitura", env={"CLOUDFLARE_ZONE_TOKEN": "zt"})
        self.assertTrue(ok)
        self.assertEqual(detalhe, ca.ROTULO_ZONA)
        self.assertTrue(urls[0].endswith("/user/tokens/verify"), urls)

    def test_verificar_com_global_key_bate_em_user(self):
        urls = []

        def urlopen_falso(req, timeout=None):
            urls.append(req.full_url)
            return _RespostaFalsa({"success": True})

        with mock.patch("cloudflare_auth.urllib.request.urlopen", side_effect=urlopen_falso):
            ok, detalhe = ca.verificar(
                "firewall", env={"CLOUDFLARE_EMAIL": "a@b.com", "CLOUDFLARE_API_TOKEN": "gk"})
        self.assertTrue(ok)
        self.assertEqual(detalhe, ca.ROTULO_GLOBAL)
        self.assertTrue(urls[0].endswith("/user"))
        self.assertFalse(urls[0].endswith("/tokens/verify"))

    def test_verificar_usa_cache_na_segunda_chamada(self):
        chamadas = {"n": 0}

        def urlopen_falso(req, timeout=None):
            chamadas["n"] += 1
            return _RespostaFalsa({"success": True})

        with mock.patch("cloudflare_auth.urllib.request.urlopen", side_effect=urlopen_falso):
            ca.verificar("leitura", env={"CLOUDFLARE_ZONE_TOKEN": "zt"})
            ca.verificar("leitura", env={"CLOUDFLARE_ZONE_TOKEN": "zt"})
        self.assertEqual(chamadas["n"], 1, "segunda chamada deveria vir do cache de 1h")


# --- identidade de saida ----------------------------------------------------


class IdentidadeDeSaida(_BaseIsolada):
    """AO SAIR PARA A REDE, O PORTAL E O WikijuridicaBot (CLAUDE.md secao 11).

    Ate 2026-09-10 as 17 ferramentas de borda que consomem este modulo
    falavam com api.cloudflare.com sem User-Agent nenhum, e o urllib mandava
    `Python-urllib/3.11`. O gate `check-identidade-de-saida` nao via porque so
    avaliava arquivo que DEFINE um User-Agent — ausencia escapava da regua que
    existe justamente para cobrar identidade.

    PROVA POR MUTACAO: apagar `"User-Agent": identidade` de qualquer um dos tres
    retornos de `cabecalhos()` deixa `test_todo_escopo_com_credencial_leva_a_identidade`
    vermelho; trocar o propósito de um escopo deixa
    `test_proposito_sai_do_escopo` vermelho; e tirar o `headers=cab` do
    `Request` deixa `test_a_requisicao_montada_leva_a_identidade` vermelho.
    """

    CANONICO = re.compile(
        r"^Mozilla/5\.0 \(compatible; WikijuridicaBot/\d+\.\d+; "
        r"\+https://wikijuridica\.com\.br/bot/; [a-z0-9][a-z0-9 .,:/-]*\)$")

    def test_todo_escopo_com_credencial_leva_a_identidade(self):
        env = {"CLOUDFLARE_ZONE_TOKEN": "zt", "CLOUDFLARE_EMAIL": "a@b.com",
               "CLOUDFLARE_API_TOKEN": "gk"}
        for escopo in ("leitura", "purga", "escrita", "firewall"):
            with self.subTest(escopo=escopo):
                cab, rotulo = ca.cabecalhos(escopo, env=env)
                self.assertIsNotNone(cab)
                self.assertNotEqual(rotulo, ca.ROTULO_AUSENTE)
                self.assertIn("User-Agent", cab)
                self.assertNotIn("Python-urllib", cab["User-Agent"])
                self.assertRegex(cab["User-Agent"], self.CANONICO)

    def test_identidade_vale_tambem_quando_cai_para_a_global_key(self):
        """A queda de credencial nao pode levar a identidade junto: sem o token
        de zona, `leitura` resolve pela Global Key — e continua se apresentando."""
        cab, rotulo = ca.cabecalhos(
            "leitura", env={"CLOUDFLARE_EMAIL": "a@b.com", "CLOUDFLARE_API_TOKEN": "gk"})
        self.assertEqual(rotulo, ca.ROTULO_GLOBAL)
        self.assertRegex(cab["User-Agent"], self.CANONICO)

    def test_proposito_sai_do_escopo(self):
        """O proposito e SEMANTICO: quem le metrica nao e quem purga cache nem
        quem reescreve ruleset, e e isso que o operador do outro lado distingue
        no log. Deriva-lo do escopo evita um parametro novo nos 17
        chamadores — e evita que 16 deles esquecam de passa-lo."""
        self.assertTrue(ca.user_agent("leitura").endswith("; medicao-de-borda)"))
        self.assertTrue(ca.user_agent("purga").endswith("; purga-de-borda)"))
        self.assertTrue(ca.user_agent("escrita").endswith("; regras-de-borda)"))
        self.assertTrue(ca.user_agent("firewall").endswith("; regras-de-borda)"))

    def test_proposito_explicito_sobrescreve_o_do_escopo(self):
        ua = ca.user_agent("leitura", proposito="reconciliacao-de-rastreio")
        self.assertTrue(ua.endswith("; reconciliacao-de-rastreio)"), ua)
        self.assertRegex(ua, self.CANONICO)

    def test_escopo_invalido_continua_recusado(self):
        with self.assertRaises(ValueError):
            ca.user_agent("qualquer-coisa-que-nao-e-escopo")

    def test_nao_se_apresenta_como_navegador_nem_como_bot_de_terceiro(self):
        for escopo in ("leitura", "purga", "escrita", "firewall"):
            ua = ca.user_agent(escopo)
            for proibido in ("Chrome/", "Safari/", "Firefox/", "Edg/",
                             "Googlebot", "GPTBot", "ClaudeBot", "bingbot"):
                self.assertNotIn(proibido, ua)

    def test_a_requisicao_montada_leva_a_identidade(self):
        """Dubla `urlopen` UM NIVEL ABAIXO e le o `Request` que o modulo montou:
        cabecalho que existe no dict e nao chega ao pedido nao identifica
        ninguem. Nada sai da maquina."""
        capturadas = []

        def urlopen_falso(req, timeout=None):
            capturadas.append(req)
            return _RespostaFalsa({"success": True, "result": []})

        with mock.patch("cloudflare_auth.urllib.request.urlopen", side_effect=urlopen_falso):
            ca.pega(ca.API + "/zones", "leitura", env={"CLOUDFLARE_ZONE_TOKEN": "zt"})
            ca.graphql("query { x }", {}, "leitura", env={"CLOUDFLARE_ZONE_TOKEN": "zt"})

        self.assertEqual(len(capturadas), 2)
        for pedido in capturadas:
            # urllib normaliza o nome do cabecalho para "User-agent".
            enviado = pedido.get_header("User-agent")
            self.assertIsNotNone(
                enviado, "requisicao sem User-Agent: o urllib mandaria Python-urllib")
            self.assertRegex(enviado, self.CANONICO)


if __name__ == "__main__":
    unittest.main(verbosity=1)
