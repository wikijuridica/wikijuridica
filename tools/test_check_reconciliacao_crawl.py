#!/usr/bin/env python3
"""Teste de tools/check-reconciliacao-crawl.

RODAR:  python3 tools/test_check_reconciliacao_crawl.py

TOTALMENTE OFFLINE. Nenhum caso toca a rede, o .env.local, o log real do nginx
ou as faixas de IP versionadas: cada teste monta o seu proprio diretorio
temporario com log sintetico, faixa de IP declarada e resposta GraphQL gravada,
e invoca a ferramenta como SUBPROCESSO — o mesmo comando que o operador roda,
com o exit code de verdade. Testar `main()` importado deixaria `sys.exit(main())`
sem cobertura, que e justamente a linha que decide 0, 1 ou 2.

★ POR QUE METADE DOS CASOS E DE FALSO POSITIVO

A regra do repositorio: "detector novo nasce com teste de falso positivo sobre
amostra real, e o teste tem de REPROVAR o comportamento errado". Ja houve aqui
detector que acusou 46 paginas sendo que as 46 eram falso positivo. Por isso
cada caso abaixo afirma o exit code CERTO **e nega explicitamente o errado**:
nao basta "nao deu 0", tem de nao ser 1 quando a resposta correta e 2.

A ANCORA EMPIRICA dos numeros deste arquivo e a medicao de 2026-08-27 (dia UTC
fechado, Googlebot), tirada da API viva e do log de origem no mesmo instante:

    (a) origem com IP conferido .... 13
    (b) borda total verificada ..... 19
    (c) borda com cacheStatus!=hit . 13
        hit .......................... 6
        sampleInterval medio ........ 1,0

A identidade (a) ~ (c) fecha EXATA no dado real. Os fixtures partem desses
numeros e deformam UM de cada vez, para que o que o teste mede seja a resposta
da ferramenta a deformacao, e nao a soma de varias mudancas.
"""
import datetime
import json
import os
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
FERRAMENTA = os.path.join(RAIZ, "tools", "check-reconciliacao-crawl")

# Faixa real publicada pela Google, DECLARADA aqui em vez de lida de
# data/ops/bot_ip_ranges/googlebot.json: o teste nao pode passar a falhar
# porque o arquivo de faixas foi atualizado a montante. O IP forjado usa
# 203.0.113.0/24 (TEST-NET-3, RFC 5737), que por definicao nunca sera da Google.
FAIXA_OFICIAL = "66.249.64.0/19"
IP_OFICIAL = "66.249.73.98"
IP_FORJADO = "203.0.113.7"

UA_GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
FUSO_LOG = datetime.timezone(datetime.timedelta(hours=-3))


def dia_fechado():
    """O ultimo dia UTC fechado — o mesmo padrao que a ferramenta usa.

    Data relativa, nunca fixa: a ferramenta recusa dia fora da retencao de 8
    dias da Cloudflare, entao uma data literal faria a suite verde de hoje
    virar vermelha na semana que vem sem nada ter mudado no codigo.
    """
    return (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)).date()


def linha_log(instante_utc, ip, ua, path="/", status=200):
    """Uma linha no formato `log_format wj_main` do vhost vivo, em horario local."""
    local = instante_utc.astimezone(FUSO_LOG)
    return ('%s - [%s] host=wikijuridica.com.br "GET %s HTTP/1.1" %d 27020 "%s" '
            'allow=1 bot_sim=- rt=0.000 cf_ray=a3211ee3f867eff7-GIG reqlen=566 '
            'ref="-" warm=- inm=- ims=-\n'
            % (ip, local.strftime("%d/%b/%Y:%H:%M:%S %z"), path, status, ua))


def escrever_log(destino, dia, requisicoes_oficiais, requisicoes_forjadas=0,
                 cobrir_inicio=True):
    """Log sintetico de um dia UTC, com cobertura comprovada da janela.

    A PRIMEIRA linha e deliberadamente do dia ANTERIOR: a ferramenta so aceita
    medir a origem quando algum arquivo comeca ANTES da janela, porque log que
    comeca no meio do dia produziria contagem baixa com cara de medicao boa.
    """
    ini = datetime.datetime.combine(dia, datetime.time.min, datetime.timezone.utc)
    linhas = []
    if cobrir_inicio:
        linhas.append(linha_log(ini - datetime.timedelta(hours=2), "127.0.0.1",
                                "wikijuridica-watchdog/1.0 (+interno; nao-indexar)"))
    # Espalhadas a partir das 06:04 UTC — o horario em que as chegadas do
    # Googlebot realmente comecaram em 2026-08-28, e que a janela grampeada em
    # 04:10 UTC nao alcancava. O passo e DERIVADO de N e nao fixo: com passo
    # fixo, um caso de volume alto empurraria linhas para fora do dia e a
    # contagem sairia truncada sem ninguem ver — o fixture e que estaria errado,
    # e o teste acusaria a ferramenta.
    for i in range(requisicoes_oficiais):
        passo = 17 * 3600.0 / max(1, requisicoes_oficiais)
        quando = ini + datetime.timedelta(hours=6, minutes=4, seconds=passo * i)
        linhas.append(linha_log(quando, IP_OFICIAL, UA_GOOGLEBOT,
                                "/sitemaps/pages-%04d.xml" % i, 200 if i % 2 else 304))
    for i in range(requisicoes_forjadas):
        passo = 10 * 3600.0 / max(1, requisicoes_forjadas)
        quando = ini + datetime.timedelta(hours=9, seconds=passo * i)
        linhas.append(linha_log(quando, IP_FORJADO, UA_GOOGLEBOT, "/", 200))
    # Uma linha do dia SEGUINTE: prova que o recorte da janela e por carimbo, e
    # nao "tudo que esta no arquivo".
    linhas.append(linha_log(ini + datetime.timedelta(days=1, hours=1),
                            IP_OFICIAL, UA_GOOGLEBOT, "/robots.txt", 304))
    with open(destino, "w", encoding="utf-8") as handle:
        handle.writelines(linhas)


def envelope(grupos):
    """O envelope GraphQL COMPLETO, na forma capturada da API viva em 2026-08-27.

    Guardar o envelope inteiro (data > viewer > zones > httpRequestsAdaptiveGroups)
    e nao so a lista de grupos e o que faz o fixture atravessar exatamente o
    mesmo parsing da consulta viva. Fixture com forma inventada testa um parser
    que a producao nao usa.
    """
    return {"data": {"viewer": {"zones": [{"httpRequestsAdaptiveGroups": grupos}]}},
            "errors": None}


def grupo(count, cache_status, categoria="Search Engine Crawler", intervalo=1):
    return {"count": count, "avg": {"sampleInterval": intervalo},
            "dimensions": {"cacheStatus": cache_status, "verifiedBotCategory": categoria}}


class Cenario(object):
    """Um diretorio temporario com log, faixas e fixture prontos."""

    def __init__(self, pasta, dia):
        self.pasta = pasta
        self.dia = dia
        self.log_dir = os.path.join(pasta, "log")
        self.faixas_dir = os.path.join(pasta, "faixas")
        os.makedirs(self.log_dir)
        os.makedirs(self.faixas_dir)
        with open(os.path.join(self.faixas_dir, "googlebot.json"), "w",
                  encoding="utf-8") as handle:
            json.dump({"operator": "google", "authenticates_agents": ["googlebot"],
                       "prefixes": [FAIXA_OFICIAL], "prefix_count": 1}, handle)
        self.fixture = os.path.join(pasta, "borda.json")

    def com_origem(self, oficiais, forjadas=0, cobrir_inicio=True):
        escrever_log(os.path.join(self.log_dir, "access.log"), self.dia, oficiais,
                     forjadas, cobrir_inicio)
        return self

    def sem_log(self):
        caminho = os.path.join(self.log_dir, "access.log")
        if os.path.isfile(caminho):
            os.remove(caminho)
        return self

    def com_borda(self, payload):
        with open(self.fixture, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
        return self

    def rodar(self, extra=None, usar_fixture=True, ambiente=None):
        cmd = [sys.executable, FERRAMENTA, "--data", self.dia.isoformat(),
               "--crawler", "googlebot",
               "--log-dir", self.log_dir, "--ranges-dir", self.faixas_dir,
               "--env-file", os.path.join(self.pasta, "env-inexistente")]
        if usar_fixture:
            cmd += ["--graphql-fixture", self.fixture]
        cmd += list(extra or [])
        # Ambiente limpo por padrao: sem CLOUDFLARE_*, sem PATH herdado que
        # pudesse trazer credencial de perfil. Nenhum caso deve alcancar a rede.
        env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C.UTF-8"}
        env.update(ambiente or {})
        return subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=120)


class TesteReconciliacaoCrawl(unittest.TestCase):

    def cenario(self):
        pasta = tempfile.mkdtemp(prefix="reconc-crawl-")
        self.addCleanup(__import__("shutil").rmtree, pasta, True)
        return Cenario(pasta, dia_fechado())

    # ---------------------------------------------------------------- caso 1
    def test_identidade_fecha_dentro_da_tolerancia(self):
        """origem=13, borda nao-hit=14, sampleInterval=1 -> PASSA.

        A borda ficando 1 acima e o desvio ESPERADO, nao anomalia: requisicao
        que a borda termina sozinha (bloqueio, redirecionamento) conta em (c) e
        nunca chega a origem. Com k=14 e s=1 a tolerancia e 3*sqrt(14) = 11,2.
        """
        c = self.cenario().com_origem(13).com_borda(
            envelope([grupo(14, "miss"), grupo(6, "hit")]))
        r = c.rodar()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("OK", r.stdout)
        # A saida TEM de mostrar (b) e o absorvido pelo cache: sem eles, um
        # leitor ve (a)=13 < (b)=20 e conclui de novo que "o bot sumiu".
        self.assertIn("absorvido pelo cache", r.stdout)

    # ---------------------------------------------------------------- caso 2
    def test_divergencia_real_reprova(self):
        """origem=13, borda nao-hit=200 -> REPROVA.

        187 de diferenca contra tolerancia de 3*sqrt(200) = 42,4. A borda diz
        que 200 requisicoes NAO foram servidas de cache, logo tinham de ter
        chegado ao nginx, e so 13 chegaram: ou o log nao esta sendo lido, ou os
        dois lados estao filtrando agentes diferentes. Instrumento, nao bot.
        """
        c = self.cenario().com_origem(13).com_borda(
            envelope([grupo(200, "miss"), grupo(6, "hit")]))
        r = c.rodar()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("FAIL", r.stdout)
        self.assertIn("DIVERGENCIA REAL", r.stdout)
        self.assertIn("defeito de INSTRUMENTO", r.stdout)

    def test_borda_zero_contra_origem_treze_reprova(self):
        """O defeito que originou a ferramenta, na versao de dia fechado.

        Foi exatamente este par (ledger 0, origem 13) que ficou irreconciliado
        em 2026-08-28. Com k=0 a tolerancia cai para o piso 5, e |13-0| = 13
        passa dele. Se o piso fosse generoso a ponto de absorver 13, a
        ferramenta nasceria cega para o proprio defeito que veio apanhar.
        """
        c = self.cenario().com_origem(13).com_borda(envelope([grupo(6, "hit")]))
        r = c.rodar()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    # ------------------------------------------------------ FALSO POSITIVO 1
    def test_falso_positivo_dia_corrente_e_recusado(self):
        """Dia parcial NAO pode ser avaliado — e a propria armadilha auditada.

        Avaliar hoje compararia a origem, que continua recebendo, com uma janela
        de borda que termina no instante da consulta: o mesmo `fim = agora` de
        measure-crawl-coverage:287-289, cometido por quem veio audita-lo. E
        INCONCLUSIVO (2), nunca reprovacao (1): nao ha defeito nenhum em o dia
        ainda nao ter acabado.
        """
        hoje = datetime.datetime.now(datetime.timezone.utc).date()
        c = self.cenario().com_origem(13).com_borda(envelope([grupo(13, "miss")]))
        r = c.rodar(extra=["--data", hoje.isoformat()])
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertNotEqual(r.returncode, 1, "dia parcial nao e reprovacao")
        self.assertIn("INCONCLUSIVO", r.stdout)
        self.assertIn("ainda nao fechou em UTC", r.stdout)
        # Mensagem que nao diz qual dia usar faz o operador tentar de novo igual.
        self.assertIn(dia_fechado().isoformat(), r.stdout)

    def test_falso_positivo_dia_futuro_e_recusado(self):
        """Data futura tambem e inconclusiva, nao reprovacao."""
        futuro = datetime.datetime.now(datetime.timezone.utc).date() + datetime.timedelta(days=3)
        c = self.cenario().com_origem(13).com_borda(envelope([grupo(13, "miss")]))
        r = c.rodar(extra=["--data", futuro.isoformat()])
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)

    # ------------------------------------------------------ FALSO POSITIVO 2
    def test_falso_positivo_sem_credencial_e_inconclusivo(self):
        """Sem credencial -> exit 2, JAMAIS 1.

        Reprovar por indisponibilidade de API ja foi defeito medido neste
        repositorio. Um gate que fica vermelho quando falta credencial ensina o
        operador a ignorar o vermelho — e ai o vermelho verdadeiro passa
        despercebido. Este caso roda SEM fixture, para alcancar de fato o
        caminho da credencial, e mesmo assim nao toca a rede: a ferramenta
        desiste antes de montar a requisicao.
        """
        c = self.cenario().com_origem(13).com_borda(envelope([grupo(13, "miss")]))
        r = c.rodar(usar_fixture=False)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertNotEqual(r.returncode, 1, "falta de credencial nao e veredito")
        self.assertIn("sem credencial", r.stdout)

    def test_falso_positivo_erro_de_rede_e_inconclusivo(self):
        """Erro do GraphQL vem no envelope e sai como 2, nao como 1."""
        c = self.cenario().com_origem(13).com_borda(
            {"data": None, "errors": [{"message": "cannot request a time range wider than 1d"}]})
        r = c.rodar()
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("nao e veredito sobre o crawler", r.stdout)

    def test_falso_positivo_log_ausente_e_inconclusivo(self):
        """Origem 0 por falta de log NAO pode virar PASS nem FAIL silencioso.

        Origem 0 porque o log sumiu e origem 0 porque o bot nao veio sao fatos
        opostos. Devolver o mesmo numero para os dois seria a proxima medicao
        enganosa desta serie.
        """
        c = self.cenario().sem_log().com_borda(envelope([grupo(13, "miss")]))
        r = c.rodar()
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("origem nao medivel", r.stdout)

    # ------------------------------------------------------ FALSO POSITIVO 3
    def test_falso_positivo_origem_maior_que_borda_passa(self):
        """origem=20 > borda nao-hit=14 NAO e defeito enquanto couber na tolerancia.

        O dataset da borda e AMOSTRADO e o log de origem e CENSO: a borda pode
        legitimamente ficar abaixo. Se o criterio fosse `c >= a`, todo dia de
        amostragem alta viraria reprovacao — e o operador aprenderia a ignorar.
        Com k=14 e s=1 a tolerancia e 11,2, e a diferenca de 6 cabe nela.
        """
        c = self.cenario().com_origem(20).com_borda(
            envelope([grupo(14, "miss"), grupo(6, "hit")]))
        r = c.rodar()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotEqual(r.returncode, 1, "origem acima da borda amostrada nao e defeito")

    def test_falso_positivo_amostragem_alta_nao_reprova(self):
        """s=10: 3 grupos amostrados viram 30 estimados contra 26 na origem.

        Sem multiplicar pelo sampleInterval a borda apareceria como 3 contra 26
        e a ferramenta gritaria defeito num dia perfeitamente normal.
        """
        c = self.cenario().com_origem(26).com_borda(
            envelope([grupo(3, "miss", intervalo=10), grupo(1, "hit", intervalo=10)]))
        r = c.rodar()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    # ------------------------------------------- anti-inflacao e higiene
    def test_ip_forjado_nao_entra_na_contagem_de_origem(self):
        """A conferencia de IP e o que impede a inflacao de 177x.

        13 requisicoes de IP oficial + 40 do mesmo User-Agent vindas de
        203.0.113.7 (TEST-NET-3). A ferramenta tem de contar 13 e exibir 53 como
        'por string de UA' — o contraste e o que torna a inflacao visivel em vez
        de silenciosa. Se contasse por string, |53-14| = 39 reprovaria um dia bom.
        """
        c = self.cenario().com_origem(13, forjadas=40).com_borda(
            envelope([grupo(14, "miss"), grupo(6, "hit")]))
        r = c.rodar(extra=["--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        dados = json.loads(r.stdout)
        self.assertEqual(dados["a_origem_ip_conferido"], 13)
        self.assertEqual(dados["a_origem_por_string_ua"], 53)

    def test_categoria_vazia_e_descartada_e_relatada(self):
        """Cliente que a Cloudflare NAO autenticou nao entra na conta.

        Categoria vazia e UA forjado ou sonda nossa: em nenhum dos casos e
        rastreio. Mas o volume descartado e RELATADO, porque descarte silencioso
        e a origem da proxima medicao enganosa.
        """
        c = self.cenario().com_origem(13).com_borda(envelope([
            grupo(14, "miss"), grupo(6, "hit"), grupo(900, "miss", categoria="")]))
        r = c.rodar(extra=["--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        dados = json.loads(r.stdout)
        self.assertEqual(dados["borda_descartado_sem_categoria"], 900)
        self.assertEqual(dados["c_borda_nao_hit_estimado"], 14)

    def test_recorte_da_janela_e_por_carimbo_utc(self):
        """As linhas do dia anterior e do seguinte ficam de fora.

        O log e local (-0300) e a janela e UTC. O log sintetico tem uma linha do
        dia seguinte de proposito: se a ferramenta contasse 'o arquivo inteiro'
        ou somasse 3 horas na mao, ela apareceria na conta.
        """
        c = self.cenario().com_origem(13).com_borda(
            envelope([grupo(14, "miss"), grupo(6, "hit")]))
        r = c.rodar(extra=["--json"])
        dados = json.loads(r.stdout)
        self.assertEqual(dados["a_origem_ip_conferido"], 13)
        self.assertEqual(dados["window_utc"][0], "%sT00:00:00Z" % dia_fechado().isoformat())

    def test_fora_da_retencao_e_inconclusivo(self):
        """Dia alem dos 8 dias do dataset -> 2, e ANTES de gastar cota."""
        velho = dia_fechado() - datetime.timedelta(days=30)
        c = self.cenario().com_origem(13).com_borda(envelope([grupo(13, "miss")]))
        r = c.rodar(extra=["--data", velho.isoformat()])
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("retem 8 dias", r.stdout)

    def test_falso_positivo_log_que_nao_cobre_o_inicio_da_janela(self):
        """Log que EXISTE mas comeca depois do inicio do dia -> 2, nao 0.

        Este e o caso traicoeiro: o arquivo esta la, tem mtime recente, tem
        linhas do Googlebot, e a contagem sai um numero de aparencia perfeita —
        so que a madrugada foi rotacionada para fora do disco. Sem a guarda de
        cobertura a ferramenta compararia meia origem com uma borda inteira e
        chamaria de OK, ou acusaria o crawler por um buraco que e do logrotate.

        Aqui a origem sintetica tem 13 linhas e a borda 14: SEM a guarda o
        resultado seria exit 0. E por isso que o caso discrimina.
        """
        c = self.cenario().com_origem(13, cobrir_inicio=False).com_borda(
            envelope([grupo(14, "miss"), grupo(6, "hit")]))
        r = c.rodar()
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertNotEqual(r.returncode, 0, "log truncado nao pode passar como OK")
        self.assertIn("comeca em", r.stdout)
        self.assertIn("nao esta no disco", r.stdout)

    def test_sample_interval_multiplica_a_contagem_da_borda(self):
        """s=10 com k=40: sem multiplicar, a borda apareceria como 40 e nao 400.

        O caso de volume baixo (3 grupos a s=10) NAO discrimina: a tolerancia
        de 3*s*sqrt(k) e larga o bastante para absorver o erro, e com razao —
        com tres amostras nao ha o que afirmar. Este caso existe porque um
        teste que nao consegue distinguir a formula certa da errada nao esta
        testando a formula.

        Origem = 400 (censo). Borda = 40 grupos a sampleInterval 10 = 400
        estimadas. Certo: |400-400| = 0, dentro da tolerancia 3*10*sqrt(40)=190.
        Errado (ignorando o intervalo): |400-40| = 360, acima dela -> a
        ferramenta acusaria defeito num dia perfeitamente normal.
        """
        c = self.cenario().com_origem(400).com_borda(
            envelope([grupo(40, "miss", intervalo=10), grupo(5, "hit", intervalo=10)]))
        r = c.rodar(extra=["--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        dados = json.loads(r.stdout)
        self.assertEqual(dados["a_origem_ip_conferido"], 400)
        self.assertEqual(dados["c_borda_nao_hit_estimado"], 400)
        self.assertEqual(dados["borda_nao_hit_amostrado"], 40)
        self.assertEqual(dados["sample_interval_medio"], 10.0)

    def test_ferramenta_e_read_only(self):
        """Um check nao escreve. Nenhum arquivo novo em data/ops/ apos rodar."""
        antes = sorted(os.listdir(os.path.join(RAIZ, "data", "ops")))
        c = self.cenario().com_origem(13).com_borda(
            envelope([grupo(14, "miss"), grupo(6, "hit")]))
        c.rodar()
        self.assertEqual(antes, sorted(os.listdir(os.path.join(RAIZ, "data", "ops"))))


if __name__ == "__main__":
    unittest.main(verbosity=2)
