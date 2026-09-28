#!/usr/bin/env python3
"""Prova de `token_de_produto` — a identidade que o ledger de candidatos grava.

O DEFEITO QUE ESTE TESTE TRAVA, medido em 2026-09-16 sobre
`data/ops/access/nginx-2026-09-15.jsonl` e sobre a borda (24h até
2026-09-16T16:00Z, `httpRequestsAdaptiveGroups`):

  1. `+http://ahrefs.com/robot/site-audit` — a URL de DOCUMENTAÇÃO que o
     operador embute no próprio User-Agent — era varrida pelo padrão de nome de
     bot, e `AhrefsSiteAudit` entrava em `bot_registry_candidates.jsonl` com
     `"token": "robot"`. Eram 1.182 requisições na origem naquele dia e 5.859 na
     borda: o MAIOR agente declarado fora do registro, gravado com o nome de um
     segmento de caminho de URL.
  2. Agente que imita navegador e se declara pelo slot `(compatible; X/versao)`
     sem sufixo "Bot" — `ChatGPT-User/1.0`, `meta-externalagent/1.1` — caía no
     balde `Mozilla`, 7.078 requisições no mesmo dia, com um `user_agent_sample`
     sorteado entre milhares.

CONTROLE POSITIVO e CONTROLE NEGATIVO andam juntos aqui de propósito: um parser
de User-Agent que só é cobrado pelo que DEVE casar vira um que casa tudo, e um
token a mais num ledger de registro é pior que um a menos — ele mente com
autoridade sobre quem visita o portal.

MUTAÇÃO PROVADA (rode `--mutantes` para reproduzir a prova em 3 s): cada um dos
três passos do parser é desligado, um por vez, e o teste TEM de ficar vermelho.
"""
import io as _io
import os
import sys
import unittest
from importlib.machinery import SourceFileLoader

RAIZ = os.environ.get("WIKI_ROOT", "/opt/wiki")
CAMINHO = os.path.join(RAIZ, "tools", "generate-bot-registry-candidates")
gerador = SourceFileLoader("gerador_bot_registry_candidates", CAMINHO).load_module()

# User-Agents LITERAIS, copiados do tráfego real — nenhum inventado. Origem:
# data/ops/access/nginx-2026-09-15.jsonl e a consulta de borda da mesma janela.
UA_AHREFS_SITE_AUDIT = (
    "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/151.0.7922.173 Mobile Safari/537.36 "
    "(compatible; AhrefsSiteAudit/6.1; +http://ahrefs.com/robot/site-audit)")
UA_SHAPBOT = ("Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); "
              "compatible; ShapBot/0.1.0")
UA_BAIDUSPIDER = ("Mozilla/5.0 (compatible; Baiduspider/2.0; "
                  "+http://www.baidu.com/search/spider.html)")
UA_BAIDU_RENDER = ("Mozilla/5.0 (compatible; Baiduspider-render/2.0; "
                   "+http://www.baidu.com/search/spider.html)")
UA_AIONBOT = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like "
              "Gecko) Chrome/126.0.0.0 Safari/537.36 (compatible; AionBot/1.0)")
UA_CHATGPT_USER = ("Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); "
                   "compatible; ChatGPT-User/1.0; +https://openai.com/bot")
UA_META_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like "
    "Gecko) Chrome/145.0.0.0 Safari/537.36 (compatible; meta-externalagent/1.1 "
    "(+https://developers.facebook.com/docs/sharing/webmasters/crawler))")
UA_SENTINEL = ("SentinelOracle/0.1 (+https://glimind.com/opt-out; "
               "liveness-only, never invokes tools)")
UA_SKYPE = ("Mozilla/5.0 (Windows NT 6.1; WOW64) SkypeUriPreview Preview/0.5 "
            "skype-url-preview@microsoft.com")
# Não é tráfego observado: é o CONTROLE que isola o passo 3 do parser. O domínio
# é `.test` (RFC 2606, reservado para teste) exatamente para não parecer um
# operador real, e o caminho repete as três palavras que o padrão de nome de
# agente procura.
UA_SO_URL_DE_DOC = ("Mozilla/5.0 (X11; Linux x86_64) "
                    "+http://exemplo.test/robot/spider-crawler")

# O QUE O PARSER TEM DE ACUSAR — token esperado por UA real.
POSITIVOS = {
    UA_AHREFS_SITE_AUDIT: "AhrefsSiteAudit",
    UA_SHAPBOT: "ShapBot",
    UA_BAIDUSPIDER: "Baiduspider",
    UA_BAIDU_RENDER: "Baiduspider-render",
    UA_AIONBOT: "AionBot",
    UA_CHATGPT_USER: "ChatGPT-User",
    UA_META_AGENT: "meta-externalagent",
    UA_SENTINEL: "SentinelOracle",
    UA_SKYPE: "SkypeUriPreview",
    "mcpbeat/0.1 (+https://mcpbeat.com/bot/; liveness check)": "mcpbeat",
    "Mozilla/5.0 (…) GolemreachTrustBot": "GolemreachTrustBot",
    # Cliente genérico se declara pelo primeiro token e continua contado à
    # parte — nunca dissolvido num balde com nome de bot.
    "node": "node",
    "curl/8.5.0": "curl",
    "undici": "undici",
    "Go-http-client/2.0": "Go-http-client",
    "python-httpx/0.28.1": "python-httpx",
}

# O QUE O PARSER NÃO PODE ACUSAR — navegador real. Devolver um token aqui é o
# defeito nº 2 acima: um rótulo com autoridade sobre milhares de pessoas.
NEGATIVOS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like "
    "Gecko) Chrome/153.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like "
    "Gecko) Chrome/153.0.0.0 Safari/537.36 Edg/153.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 "
    "Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 "
    "Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/152.0.0.0 Mobile Safari/537.36",
    "",
    "   ",
    None,
    # A URL de DOCUMENTAÇÃO sozinha, sem slot `compatible;`: é este caso que
    # mata o mutante `url_nao_e_removida`. Sem ele o mutante SOBREVIVIA, porque
    # no UA real do AhrefsSiteAudit o slot `compatible;` já decide antes — a
    # fixture, e não o predicado, é que estava cega (medido em 2026-09-16).
    UA_SO_URL_DE_DOC,
]


class TokenDeProduto(unittest.TestCase):
    def test_positivos_recebem_o_token_do_agente(self):
        for ua, esperado in POSITIVOS.items():
            with self.subTest(ua=ua[:60]):
                self.assertEqual(gerador.token_de_produto(ua), esperado)

    def test_negativos_nao_viram_token(self):
        for ua in NEGATIVOS:
            with self.subTest(ua=(ua or "")[:60]):
                self.assertIsNone(gerador.token_de_produto(ua))

    def test_url_de_documentacao_nunca_vira_identidade(self):
        """O caso que originou o conserto, isolado.

        Não basta `AhrefsSiteAudit` sair certo: o teste tem de morrer se o
        parser voltar a ler DENTRO da URL. Por isso o UA abaixo não tem slot
        `compatible;` nenhum — só a URL — e a resposta certa é None, nunca
        `robot`, `crawler` ou `spider`.
        """
        self.assertIsNone(gerador.token_de_produto(UA_SO_URL_DE_DOC))

    def test_slot_compatible_vence_o_sufixo_dentro_da_url(self):
        """Ordem dos passos: o slot `compatible;` decide antes do sufixo.

        No UA do AhrefsSiteAudit os dois competem — `AhrefsSiteAudit` no slot e
        `robot` na URL. Se a ordem inverter, o token volta a ser `robot`.
        """
        self.assertEqual(gerador.token_de_produto(UA_AHREFS_SITE_AUDIT),
                         "AhrefsSiteAudit")

    def test_primeiro_token_vence_o_slot_compatible(self):
        """Quem se nomeia no começo da string é o produto que fez a requisição.

        `Andi-AgentSurfaceProbe/1.0 (compatible; AndiAgent/1.0; …)` tem os dois;
        a identidade do agente é a primeira, e é a que o ledger já gravou.
        """
        ua = ("Andi-AgentSurfaceProbe/1.0 (compatible; AndiAgent/1.0; "
              "+http://andisearch.com/bot)")
        self.assertEqual(gerador.token_de_produto(ua), "Andi-AgentSurfaceProbe")

    def test_probe_sai_na_forma_canonica_do_wikijuridicabot(self):
        """`sonda_200` SAI PARA A REDE (a doc do operador). O UA é contrato.

        O prefixo `Mozilla/5.0 (compatible;` não é disfarce e não é opcional:
        medido em 2026-09-05 contra planalto.gov.br, todo UA sem ele levou
        `Recv failure` do WAF (F5 BIG-IP).
        """
        self.assertTrue(gerador.PROBE_UA.startswith(
            "Mozilla/5.0 (compatible; WikijuridicaBot/1.0; "
            "+https://wikijuridica.com.br/bot/;"), gerador.PROBE_UA)
        self.assertTrue(gerador.PROBE_UA.endswith(")"), gerador.PROBE_UA)


# --------------------------------------------------------------------------
# PROVA POR MUTAÇÃO. Um teste de parser que ninguém tentou derrubar não é prova
# de nada: ele fica verde com a fixture certa e com meio predicado. Aqui cada
# passo do parser é desligado no FONTE e o módulo é recarregado — se a suíte
# continuar verde com um passo a menos, o teste não cobre aquele passo.
MUTANTES = {
    "url_nao_e_removida": (
        "PADRAO_NOME_DE_BOT.search(PADRAO_URL_NO_UA.sub(\" \", ua))",
        "PADRAO_NOME_DE_BOT.search(ua)"),
    "slot_compatible_desligado": (
        "    declarado = PADRAO_COMPATIBLE.search(ua)\n",
        "    declarado = None\n"),
    "navegador_volta_a_ser_mozilla": (
        "    achado = PADRAO_NOME_DE_BOT.search(PADRAO_URL_NO_UA.sub(\" \", ua))\n"
        "    if achado:\n"
        "        return achado.group(1)\n"
        "    return None\n",
        "    achado = PADRAO_NOME_DE_BOT.search(PADRAO_URL_NO_UA.sub(\" \", ua))\n"
        "    if achado:\n"
        "        return achado.group(1)\n"
        "    return candidato\n"),
}


def _roda_mutantes():
    import tempfile
    fonte = _io.open(CAMINHO, encoding="utf-8").read()
    falhou_algum = False
    for nome, (de, para) in MUTANTES.items():
        if fonte.count(de) != 1:
            print("MUTANTE %-34s INAPLICAVEL (âncora aparece %d vez(es))"
                  % (nome, fonte.count(de)))
            falhou_algum = True
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                         encoding="utf-8") as tmp:
            tmp.write(fonte.replace(de, para))
            caminho_mutante = tmp.name
        try:
            mutante = SourceFileLoader("mutante_" + nome,
                                       caminho_mutante).load_module()
            sobreviveu = True
            for ua, esperado in POSITIVOS.items():
                if mutante.token_de_produto(ua) != esperado:
                    sobreviveu = False
                    break
            if sobreviveu:
                for ua in NEGATIVOS:
                    if mutante.token_de_produto(ua) is not None:
                        sobreviveu = False
                        break
            print("MUTANTE %-34s %s" % (nome, "SOBREVIVEU (teste cego!)"
                                        if sobreviveu else "morto"))
            falhou_algum = falhou_algum or sobreviveu
        finally:
            os.unlink(caminho_mutante)
    return 1 if falhou_algum else 0


if __name__ == "__main__":
    if "--mutantes" in sys.argv:
        sys.exit(_roda_mutantes())
    unittest.main()
