#!/usr/bin/env python3
"""Testes dos quatro tools/check-social-*, nos dois sentidos.

O QUE ESTE ARQUIVO PROVA, e por que os dois sentidos são obrigatórios:

  VERDADEIRO POSITIVO  cada sonda REPROVA o defeito real que ela promete pegar —
                       o cache que guardou uma resposta de sessão, a CSP servida
                       divergindo da versionada, o balde que não devolve 429, o
                       cabeçalho de CORS numa rota com cookie.
  FALSO POSITIVO       nenhuma delas reprova o estado correto. Gate que acusa o
                       acerto é desligado na primeira semana, e a trava morre
                       junto.
  CÓDIGO DE SAÍDA      indisponibilidade sai 2, nunca 1. É a distinção que
                       separa "a borda está errada" de "não deu para medir", e
                       confundi-las transforma serviço fora do ar em alarme de
                       segurança — que ninguém consome depois da terceira vez.

A camada de rede é substituída por dublês: o que está sob teste é a DECISÃO da
sonda sobre a resposta, não o servidor. As asserções sobre a configuração vivem
em internal/socialborda e são testadas em Go, sobre um repositório-fixture.
"""
import importlib.machinery
import importlib.util
import os
import tempfile
import unittest

# NOTA SOBRE O IPv6 DAS FIXTURES: 2001:db8::/32 (RFC 3849) seria o certo
# para documentacao, e NAO serve aqui -- `botagents.ip_nao_publico` a
# desconta, corretamente, e a fixture de visitante humano precisa de um
# endereco que a ferramenta aceite como publico. Usa-se um /64 arbitrario
# da faixa publica, que nao e o de nenhum visitante medido: o dado pessoal
# era o bloco ESPECIFICO da pessoa observada, nao a faixa do provedor.

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def carrega(nome_do_arquivo, nome_do_modulo):
    alvo = os.path.join(RAIZ, "tools", nome_do_arquivo)
    spec = importlib.util.spec_from_loader(
        nome_do_modulo,
        importlib.machinery.SourceFileLoader(nome_do_modulo, alvo),
    )
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


cache = carrega("check-social-cache", "check_social_cache")
csp = carrega("check-social-csp", "check_social_csp")
rate = carrega("check-social-rate-bypass", "check_social_rate_bypass")
sem_cors = carrega("check-social-sem-cors", "check_social_sem_cors")

OK, ERRADO, INCONCLUSIVO = 0, 1, 2


class Dubles:
    """Substitui as funções de rede e de gate de um módulo de sonda."""

    def __init__(self, caso, modulo):
        self.caso = caso
        self.sonda = modulo.sonda
        self.originais = {}

    def troca(self, nome, valor):
        self.originais[nome] = getattr(self.sonda, nome)
        setattr(self.sonda, nome, valor)
        self.caso.addCleanup(setattr, self.sonda, nome, self.originais[nome])

    def estrutural(self, codigo, saida="saida do gate"):
        self.troca("gate_estrutural", lambda _nome: (codigo, saida))

    def portas_no_ar(self, no_ar=True):
        self.troca("escuta", lambda *_a, **_k: no_ar)


class TestMapeamentoDeCodigos(unittest.TestCase):
    """O gate estrutural manda no código de saída, e sem ambiguidade."""

    def test_estrutural_reprovado_sai_1_nos_quatro(self):
        for modulo in (cache, csp, rate, sem_cors):
            with self.subTest(modulo=modulo.NOME):
                dubles = Dubles(self, modulo)
                dubles.estrutural(ERRADO)
                dubles.portas_no_ar(True)
                self.assertEqual(modulo.main(), ERRADO)

    def test_estrutural_que_nao_rodou_sai_2_nos_quatro(self):
        """run-check saindo 75 (cache inutilizavel) ou 124 (tempo) nao e veredito
        sobre a configuracao: tratar isso como reprovacao viraria alarme falso."""
        for modulo in (cache, csp, rate, sem_cors):
            with self.subTest(modulo=modulo.NOME):
                dubles = Dubles(self, modulo)
                dubles.estrutural(INCONCLUSIVO, "tools/run-check saiu 75")
                dubles.portas_no_ar(True)
                self.assertEqual(modulo.main(), INCONCLUSIVO)

    def test_servico_fora_do_ar_sai_2_nos_quatro(self):
        for modulo in (cache, csp, rate, sem_cors):
            with self.subTest(modulo=modulo.NOME):
                dubles = Dubles(self, modulo)
                dubles.estrutural(OK)
                dubles.portas_no_ar(False)
                self.assertEqual(modulo.main(), INCONCLUSIVO)


def resposta(cabecalhos, status=200):
    """Dublê de sonda.requisita: devolve (status, dict, erro)."""
    return lambda *_a, **_k: (status, dict(cabecalhos), None)


def resposta_bruta(pares, status=200):
    """Dublê de sonda.requisita_bruto: preserva cabeçalho repetido."""
    return lambda *_a, **_k: (status, list(pares), None)


class TestCache(unittest.TestCase):
    ESTADOS_CORRETOS = ["MISS", "HIT", "BYPASS"]

    def _monta(self, estados, cache_control="private, no-store", status=200):
        dubles = Dubles(self, cache)
        dubles.estrutural(OK)
        dubles.portas_no_ar(True)
        dubles.troca("requisita", resposta({"Cache-Control": cache_control}, status))
        original = cache.le_estados_do_log
        cache.le_estados_do_log = lambda _nonce: (estados, None)
        self.addCleanup(setattr, cache, "le_estados_do_log", original)
        return dubles

    def test_anonimo_cacheia_e_sessao_nao_aprova(self):
        self._monta(self.ESTADOS_CORRETOS)
        self.assertEqual(cache.main(), OK)

    def test_sessao_servida_do_cache_reprova(self):
        """O vazamento: a requisicao com cookie recebeu HIT, ou seja, leu do
        cache o que outro visitante gravou."""
        self._monta(["MISS", "HIT", "HIT"])
        self.assertEqual(cache.main(), ERRADO)

    def test_sessao_gravada_no_cache_reprova(self):
        """proxy_cache_bypass sem proxy_no_cache: a resposta de sessao nao veio
        do cache (nao e HIT) mas ENTROU nele. O sintoma visivel e o
        Cache-Control publico na resposta autenticada."""
        self._monta(["MISS", "HIT", "MISS"], cache_control="public, max-age=600")
        self.assertEqual(cache.main(), ERRADO)

    def test_anonimo_que_nunca_cacheia_reprova(self):
        """Cache desligado nao e seguranca: serve mal o bot de alto valor, que e
        o canal de resultado do projeto."""
        self._monta(["MISS", "MISS", "BYPASS"])
        self.assertEqual(cache.main(), ERRADO)

    def test_log_ilegivel_sai_2(self):
        dubles = Dubles(self, cache)
        dubles.estrutural(OK)
        dubles.portas_no_ar(True)
        dubles.troca("requisita", resposta({"Cache-Control": "private, no-store"}))
        original = cache.le_estados_do_log
        cache.le_estados_do_log = lambda _nonce: (None, "sem permissao de leitura")
        self.addCleanup(setattr, cache, "le_estados_do_log", original)
        self.assertEqual(cache.main(), INCONCLUSIVO)


class TestLeituraDoAccessLog(unittest.TestCase):
    """le_estados_do_log e a funcao que decide o veredito do gate de cache no
    dia em que o ingress existir, e ela e a unica que os outros testes dublam.
    Aqui ela roda de verdade, sobre linhas com o formato wj_main real."""

    LINHA = ('2804:7f4::1 - [04/Sep/2026:20:46:56 -0300] host=wikijuridica.com.br '
             '"GET /redesocial/?wj_probe={nonce} HTTP/1.1" 200 3 "wikijuridica-superficie-probe/1.0" '
             'allow=0 bot_sim=- rt=0.001 cf_ray=- reqlen=527 ref="-" warm=true '
             'ae="gzip, br" ocs={estado} inm=- ims=-')

    def _com_log(self, estados, nonce="abc123"):
        arquivo = tempfile.NamedTemporaryFile("w", suffix=".log", delete=False, encoding="utf-8")
        # Linhas de OUTRAS requisicoes entram no meio: a funcao tem de filtrar
        # pelo nonce, e nao simplesmente ler as ultimas linhas do arquivo.
        arquivo.write(self.LINHA.format(nonce="de-outra-sonda", estado="HIT") + "\n")
        for estado in estados:
            arquivo.write(self.LINHA.format(nonce=nonce, estado=estado) + "\n")
            arquivo.write(self.LINHA.format(nonce="de-outra-sonda", estado="MISS") + "\n")
        arquivo.close()
        self.addCleanup(os.unlink, arquivo.name)
        original = cache.sonda.ACCESS_LOG
        cache.sonda.ACCESS_LOG = arquivo.name
        self.addCleanup(setattr, cache.sonda, "ACCESS_LOG", original)
        return nonce

    def test_le_os_tres_estados_na_ordem(self):
        nonce = self._com_log(["MISS", "HIT", "BYPASS"])
        estados, erro = cache.le_estados_do_log(nonce)
        self.assertIsNone(erro)
        self.assertEqual(estados, ["MISS", "HIT", "BYPASS"])

    def test_le_o_vazamento_quando_ele_acontece(self):
        """A sessao servida do cache: o gate precisa LER o HIT para reprova-lo."""
        nonce = self._com_log(["MISS", "HIT", "HIT"])
        estados, erro = cache.le_estados_do_log(nonce)
        self.assertIsNone(erro)
        self.assertEqual(estados, ["MISS", "HIT", "HIT"])

    def test_linhas_de_menos_sai_inconclusivo(self):
        """Buffer do nginx ainda nao descarregado nao e veredito sobre o cache."""
        nonce = self._com_log(["MISS", "HIT"])
        estados, erro = cache.le_estados_do_log(nonce, tentativas=2, espera=0.01)
        self.assertIsNone(estados)
        self.assertIn("access log", erro)

    def test_log_ausente_devolve_erro_e_nao_estados(self):
        original = cache.sonda.ACCESS_LOG
        cache.sonda.ACCESS_LOG = "/caminho/que/nao/existe/access.log"
        self.addCleanup(setattr, cache.sonda, "ACCESS_LOG", original)
        estados, erro = cache.le_estados_do_log("abc123", tentativas=1, espera=0.01)
        self.assertIsNone(estados)
        self.assertIsNotNone(erro)


class TestCSP(unittest.TestCase):
    def _politicas(self):
        publica, erro = csp.politica_do_conf(csp.CONF_PUBLICO)
        self.assertIsNone(erro, f"o .conf publico do repositorio nao pode ser ilegivel: {erro}")
        privada, erro = csp.politica_do_conf(csp.CONF_PRIVADO)
        self.assertIsNone(erro, f"o .conf privado do repositorio nao pode ser ilegivel: {erro}")
        return publica, privada

    def test_le_a_politica_real_do_conf(self):
        publica, privada = self._politicas()
        self.assertIn("default-src 'none'", publica)
        self.assertIn("default-src 'none'", privada)

    def _monta(self, monta_resposta):
        dubles = Dubles(self, csp)
        dubles.estrutural(OK)
        dubles.portas_no_ar(True)
        dubles.troca("requisita_bruto", monta_resposta)
        return dubles

    def test_politica_servida_igual_aprova(self):
        publica, privada = self._politicas()

        def responde(_porta, _caminho, metodo="GET", cabecalhos=None, timeout=10):
            tem_sessao = bool(cabecalhos and cabecalhos.get("Cookie"))
            valor = privada if tem_sessao else publica
            return 200, [("Content-Security-Policy", valor)], None

        self._monta(responde)
        self.assertEqual(csp.main(), OK)

    def test_um_byte_de_deriva_reprova(self):
        publica, privada = self._politicas()

        def responde(_porta, _caminho, metodo="GET", cabecalhos=None, timeout=10):
            tem_sessao = bool(cabecalhos and cabecalhos.get("Cookie"))
            valor = privada if tem_sessao else publica.replace("default-src 'none'", "default-src 'self'", 1)
            return 200, [("Content-Security-Policy", valor)], None

        self._monta(responde)
        self.assertEqual(csp.main(), ERRADO)

    def test_politica_repetida_reprova(self):
        """Duas CSPs na mesma resposta sao aplicadas como INTERSECAO pelo
        navegador: a pagina quebra em producao e o teste que le so o ultimo
        cabecalho passa."""
        publica, privada = self._politicas()

        def responde(_porta, _caminho, metodo="GET", cabecalhos=None, timeout=10):
            tem_sessao = bool(cabecalhos and cabecalhos.get("Cookie"))
            valor = privada if tem_sessao else publica
            return 200, [("Content-Security-Policy", valor), ("Content-Security-Policy", valor)], None

        self._monta(responde)
        self.assertEqual(csp.main(), ERRADO)

    def test_resposta_sem_politica_reprova(self):
        self._monta(resposta_bruta([("X-Content-Type-Options", "nosniff")]))
        self.assertEqual(csp.main(), ERRADO)

    def test_sessao_recebendo_a_politica_publica_reprova(self):
        """A privada e a que NUNCA pode listar host de terceiro. Servir a
        publica numa tela autenticada e a deriva que importa, mesmo enquanto as
        duas coincidirem byte a byte hoje."""
        publica, privada = self._politicas()
        if publica == privada:
            self.skipTest("as duas politicas coincidem byte a byte hoje; a troca seria indetectavel por construcao")
        self._monta(resposta_bruta([("Content-Security-Policy", publica)]))
        self.assertEqual(csp.main(), ERRADO)


class TestRateBypass(unittest.TestCase):
    NGINX_COM_BALDE = """
http {
    limit_req_zone $binary_remote_addr zone=wj_social_escrita:10m rate=60r/m;
    server {
        location ^~ /api/v1/redesocial/ {
            limit_req zone=wj_social_escrita burst=8 nodelay;
            proxy_pass http://127.0.0.1:8091;
        }
    }
}
"""

    def test_recorta_o_bloco_e_dimensiona_a_rajada(self):
        corpo = rate.bloco_da_location(self.NGINX_COM_BALDE, rate.LOCATION_DE_ESCRITA)
        self.assertIsNotNone(corpo, "o recorte nao achou o bloco de escrita")
        self.assertIn("limit_req zone=wj_social_escrita", corpo)
        self.assertNotIn("location ^~", corpo, "o recorte vazou para fora do bloco")

    def test_recorte_ignora_bloco_comentado(self):
        texto = self.NGINX_COM_BALDE.replace(
            "        location ^~ /api/v1/redesocial/ {",
            "        # exemplo: location ^~ /api/v1/redesocial/ { limit_req zone=x burst=1; }\n"
            "        location ^~ /api/v1/redesocial/ {")
        corpo = rate.bloco_da_location(texto, rate.LOCATION_DE_ESCRITA)
        self.assertIsNotNone(corpo)
        self.assertIn("wj_social_escrita", corpo)

    def _monta(self, respostas):
        dubles = Dubles(self, rate)
        dubles.estrutural(OK)
        dubles.portas_no_ar(True)
        sequencia = iter(respostas)

        def responde(*_a, **_k):
            try:
                return next(sequencia), {}, None
            except StopIteration:
                return 200, {}, None

        dubles.troca("requisita", responde)
        original = rate.dimensiona_rajada
        rate.dimensiona_rajada = lambda: (10, "wj_social_escrita", None)
        self.addCleanup(setattr, rate, "dimensiona_rajada", original)
        return dubles

    def test_balde_que_responde_429_aprova(self):
        self._monta([404] * 8 + [429])
        self.assertEqual(rate.main(), OK)

    def test_balde_que_nunca_limita_reprova(self):
        """Diretiva escrita apontando para zona grande demais passa no gate
        estrutural e nao limita nada: e o defeito que so a sonda pega."""
        self._monta([404] * 20)
        self.assertEqual(rate.main(), ERRADO)

    def test_sem_burst_declarado_sai_2(self):
        dubles = Dubles(self, rate)
        dubles.estrutural(OK)
        dubles.portas_no_ar(True)
        original = rate.dimensiona_rajada
        rate.dimensiona_rajada = lambda: (0, "", "a limit_req nao declara burst=")
        self.addCleanup(setattr, rate, "dimensiona_rajada", original)
        self.assertEqual(rate.main(), INCONCLUSIVO)

    def test_rajada_tem_teto(self):
        """Sonda sem teto, apontada para balde mal dimensionado, vira a carga que
        o balde deveria conter."""
        self.assertLessEqual(rate.TETO_DA_RAJADA, 400)

    def test_rajada_nao_forja_user_agent_de_bot(self):
        """A regra que decide o metodo deste gate: a sonda usa User-Agent
        proprio e marca a requisicao como interna."""
        self.assertIn("wikijuridica", rate.sonda.CABECALHOS_BASE["User-Agent"])
        self.assertEqual(rate.sonda.CABECALHOS_BASE["X-Warming-Request"], "true")
        for proibido in ("googlebot", "gptbot", "claudebot", "bingbot"):
            self.assertNotIn(proibido, rate.sonda.CABECALHOS_BASE["User-Agent"].lower())


class TestSemCORS(unittest.TestCase):
    def _monta(self, pares):
        dubles = Dubles(self, sem_cors)
        dubles.estrutural(OK)
        dubles.portas_no_ar(True)
        dubles.troca("requisita_bruto", resposta_bruta(pares))
        return dubles

    def test_resposta_limpa_aprova(self):
        self._monta([("Content-Type", "text/html"), ("X-Frame-Options", "DENY")])
        self.assertEqual(sem_cors.main(), OK)

    def test_allow_origin_reprova(self):
        self._monta([("Access-Control-Allow-Origin", "*")])
        self.assertEqual(sem_cors.main(), ERRADO)

    def test_allow_credentials_sozinho_reprova(self):
        """Allow-Credentials sem Allow-Origin ja denuncia que alguem ligou CORS
        nesta superficie; esperar o par completo seria esperar o vazamento."""
        self._monta([("Access-Control-Allow-Credentials", "true")])
        self.assertEqual(sem_cors.main(), ERRADO)

    def test_allow_methods_sozinho_nao_reprova(self):
        """Allow-Methods NAO autoriza origem cruzada, e o acervo o emite no
        preflight por decisao correta: acusa-lo seria o falso positivo que faz
        desligarem o gate."""
        self._monta([("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")])
        self.assertEqual(sem_cors.main(), OK)

    def test_varre_os_caminhos_de_erro(self):
        """404 e 405 entram na varredura: e onde um cabecalho escapa quando o
        middleware roda depois do roteamento."""
        self.assertIn("/redesocial/rota-que-nao-existe", sem_cors.CAMINHOS)
        self.assertIn("POST", sem_cors.METODOS)
        self.assertIn("OPTIONS", sem_cors.METODOS)

    def test_manda_origin_de_terceiro(self):
        """Sem Origin na requisicao, um middleware condicional nao emitiria o
        cabecalho e a varredura aprovaria uma superficie aberta."""
        self.assertTrue(sem_cors.ORIGEM_DE_TESTE.endswith(".invalid"))


if __name__ == "__main__":
    unittest.main()
