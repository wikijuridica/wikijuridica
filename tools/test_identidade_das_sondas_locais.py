#!/usr/bin/env python3
"""Prova que as SONDAS DE SERVIÇO LOCAL saem identificadas — sem tocar a rede real.

POR QUE ESTE ARQUIVO EXISTE (2026-09-10)
----------------------------------------
`tools/check-identidade-de-saida` reprovava identidade ERRADA e absolvia
identidade AUSENTE (`if not agentes: return [], False`). Com o buraco fechado,
a varredura achou 31 ferramentas mudas em `tools/`. As que falam com terceiro
foram corrigidas com o User-Agent canônico do WikijuridicaBot; as que sondam
serviço NOSSO na máquina foram corrigidas com a sonda interna que o contrato
nomeia (CLAUDE.md seção 11):

    wikijuridica-superficie-probe/1.0

Sonda anônima não é só falta de educação: quando o alvo é o portal, o
`X-Warming-Request` é o que `internal/httpserver/access_log.go` lê para gravar
`warming=true` e manter a requisição FORA da contagem de tráfego. Sem ele o
portal mede o próprio eco. Quando o alvo é outro serviço local (Ollama,
llama-server, cloudflared), não há audiência a proteger e o cabeçalho não vai —
mas o nome continua indo, porque é o que separa a nossa sonda de um cliente
qualquer da máquina no log daquele serviço.

COMO SE PROVA AQUI
------------------
A rede é dublada UM NÍVEL ABAIXO — em `urllib.request.urlopen`, dentro do módulo
carregado — e o `Request` que a ferramenta montou é lido. Nada sai da máquina, e
nenhum serviço precisa estar de pé.

Para as ferramentas em shell, um servidor HTTP de mentira sobe numa porta livre,
o endpoint é apontado para ele por variável de ambiente e o teste lê o
User-Agent que o servidor RECEBEU — que é a única prova de que a opção `-A`
chegou ao fio.

PROVA POR MUTAÇÃO. Cada caso fica vermelho quando a identidade é removida da
ferramenta correspondente:

    cp tools/check-tunnel-health /tmp/x
    sed -i 's/, headers=CABECALHOS_SONDA//' /tmp/x   # e aponte o teste para /tmp/x
"""
from __future__ import annotations

import http.server
import importlib.machinery
import importlib.util
import io
import os
import pathlib
import re
import shutil
import signal
import socket
import subprocess
import tempfile
import threading
import time
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SONDA = "wikijuridica-superficie-probe/1.0"

# A forma que `internal/wikijuridicabot.UserAgentComProposito` produz, e que o
# gate `tools/check-identidade-de-saida` cobra.
CANONICO = re.compile(
    r"^Mozilla/5\.0 \(compatible; WikijuridicaBot/\d+\.\d+; "
    r"\+https://wikijuridica\.com\.br/bot/; [a-z0-9][a-z0-9 .,:/-]*\)$")


def carrega(nome_arquivo):
    """Carrega uma ferramenta de `tools/` como módulo, pelo caminho."""
    caminho = str(RAIZ / "tools" / nome_arquivo)
    loader = importlib.machinery.SourceFileLoader(
        "sonda_" + nome_arquivo.replace("-", "_"), caminho)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


class RespostaFalsa(io.BytesIO):
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
        return False


class _DublaUrlopen:
    """Substitui `urlopen` NO MÓDULO carregado e guarda o que foi pedido."""

    def __init__(self, modulo, corpo=b"{}"):
        self.modulo = modulo
        self.corpo = corpo
        self.pedidos = []

    def __enter__(self):
        self._original = self.modulo.urllib.request.urlopen

        def falso(requisicao, timeout=None):
            self.pedidos.append(requisicao)
            return RespostaFalsa(self.corpo)

        self.modulo.urllib.request.urlopen = falso
        return self

    def __exit__(self, *_):
        self.modulo.urllib.request.urlopen = self._original
        return False

    def agente_do(self, indice=0):
        # urllib normaliza o nome do cabeçalho para "User-agent".
        return self.pedidos[indice].get_header("User-agent")


class SondasEmPython(unittest.TestCase):

    def afirma_sonda(self, dupla, quantos=1):
        self.assertGreaterEqual(len(dupla.pedidos), quantos)
        for indice in range(len(dupla.pedidos)):
            agente = dupla.agente_do(indice)
            self.assertIsNotNone(
                agente,
                "pedido %d saiu sem User-Agent: o urllib mandaria Python-urllib"
                % indice)
            self.assertEqual(agente, SONDA, "a sonda contratual é a do contrato, seção 11")

    # ── SONDA DO PRÓPRIO PORTAL: o UA não basta, o X-Warming-Request é o que
    # mantém a requisição FORA da contagem de audiência. Os dois casos abaixo
    # nasceram de uma medição, não de revisão de código: em 2026-09-16
    # `tools/check-sonda-interna-declarada` achou 193 requisições de
    # `wikijuridica-reload-check/1.0` em 7 dias (~24/dia, TODO dia) gravadas com
    # `warming=false` — o portal media o próprio eco de verdade, e ninguém via.
    #
    # PROVA POR MUTAÇÃO: remova `"X-Warming-Request": "true"` do dicionário em
    # `tools/reload-wiki-server:markdown_responde` e este caso fica vermelho.

    def afirma_sonda_do_portal(self, dupla, indice=0):
        """Quem sonda o PORTAL declara as duas marcas: nome e aquecimento."""
        pedido = dupla.pedidos[indice]
        agente = pedido.get_header("User-agent")
        self.assertIsNotNone(agente, "pedido saiu sem User-Agent")
        self.assertTrue(
            agente.lower().startswith("wikijuridica"),
            "sonda do portal tem de se nomear; veio %r" % agente)
        self.assertEqual(
            pedido.get_header("X-warming-request"), "true",
            "sem X-Warming-Request a sonda entra na metrica e o portal mede o "
            "proprio eco — internal/httpserver/access_log.go le este cabecalho "
            "para gravar warming=true")

    def test_reload_wiki_server_sonda_a_gemea_fora_da_metrica(self):
        modulo = carrega("reload-wiki-server")
        with _DublaUrlopen(modulo, b"# Titulo\n\ncorpo\n") as dupla:
            modulo.markdown_responde("/familia/x/", timeout=1)
        self.afirma_sonda_do_portal(dupla)

    def test_check_api_catalog_usage_le_o_proprio_catalogo_fora_da_metrica(self):
        modulo = carrega("check-api-catalog-usage")
        with _DublaUrlopen(modulo, b'{"linkset": []}') as dupla:
            modulo.fetch_catalog("http://127.0.0.1:8089/.well-known/api-catalog",
                                 timeout=1)
        self.afirma_sonda_do_portal(dupla)

    def test_check_tunnel_health_le_json_identificado(self):
        modulo = carrega("check-tunnel-health")
        with _DublaUrlopen(modulo, b'{"readyConnections": 4}') as dupla:
            modulo.ler_json("http://127.0.0.1:20243/ready", timeout=1)
        self.afirma_sonda(dupla)

    def test_check_tunnel_health_le_metricas_identificado(self):
        modulo = carrega("check-tunnel-health")
        with _DublaUrlopen(modulo, b"# HELP x\n") as dupla:
            modulo.ler_metricas(timeout=1)
        self.afirma_sonda(dupla)

    def test_check_tunnel_replica_fleet_consulta_identificada(self):
        modulo = carrega("check-tunnel-replica-fleet")
        with _DublaUrlopen(modulo, b'{"readyConnections": 4, "connectorId": "c"}') as dupla:
            modulo.consulta(20251, timeout=1)
        self.afirma_sonda(dupla)

    def test_generate_medicao_runner_local_pergunta_ao_ollama_identificado(self):
        modulo = carrega("generate-medicao-runner-local")
        with _DublaUrlopen(modulo, b'{"models": []}') as dupla:
            modulo.residentes_no_ollama()
        self.afirma_sonda(dupla)

    def test_generate_medicao_runner_local_completa_identificado(self):
        """O POST de geração é o pedido mais caro que esta ferramenta faz —
        e era o mais anônimo: ia com `Content-Type` e nada mais."""
        modulo = carrega("generate-medicao-runner-local")
        with _DublaUrlopen(modulo, b'{"content": "x"}') as dupla:
            modulo.completa(18080, "prompt", 4, 5)
        self.afirma_sonda(dupla)
        self.assertEqual(dupla.pedidos[0].get_header("Content-type"),
                         "application/json",
                         "a identidade não pode ter substituído o cabeçalho que já existia")

    def test_check_dns_aid_consulta_doh_como_wikijuridicabot(self):
        """DoH sai para TERCEIRO (cloudflare-dns.com, dns.google), então aqui a
        identidade é a canônica do WikijuridicaBot, não a sonda interna."""
        modulo = carrega("check-dns-aid")
        with _DublaUrlopen(modulo, b'{"Status": 0, "AD": true}') as dupla:
            modulo.doh("wikijuridica.com.br", "SVCB")
        self.assertEqual(len(dupla.pedidos), 1)
        agente = dupla.agente_do()
        self.assertIsNotNone(agente, "consulta DoH anônima: o urllib mandaria Python-urllib")
        self.assertRegex(agente, CANONICO)
        self.assertTrue(agente.endswith("; verificacao-dnssec)"), agente)
        self.assertEqual(dupla.pedidos[0].get_header("Accept"), "application/dns-json",
                         "a identidade não pode ter substituído o cabeçalho que já existia")


class ComandosDeSubprocesso(unittest.TestCase):
    """Ferramenta que chama `curl` por lista de argumentos.

    Aqui o `argv` É o comando: se `-A` está na lista, o curl o recebe. Dublar
    `rodar` prova isso sem subir nada e sem gastar os 25 MB da medição real.
    """

    def comando_de(self, modulo, funcao_nome, *args):
        comandos = []

        def rodar_falso(comando, timeout=None):
            comandos.append(list(comando))
            return 0, "0 0 0", ""

        original = modulo.rodar
        modulo.rodar = rodar_falso
        try:
            getattr(modulo, funcao_nome)(*args)
        finally:
            modulo.rodar = original
        return comandos

    def afirma_agente_no_argv(self, comando, esperado):
        self.assertIn("-A", comando, "curl sem `-A`: sai como curl/8.x")
        self.assertEqual(comando[comando.index("-A") + 1], esperado)

    def test_measure_uplink_throughput_mede_como_wikijuridicabot(self):
        modulo = carrega("measure-uplink-throughput")
        for funcao in ("medir_descida", "medir_subida"):
            with self.subTest(funcao=funcao):
                comandos = self.comando_de(modulo, funcao, 1024, 5)
                self.assertEqual(len(comandos), 1)
                self.afirma_agente_no_argv(comandos[0], modulo.USER_AGENT)
                self.assertRegex(modulo.USER_AGENT, CANONICO)

    def test_switch_uplink_band_sonda_o_cloudflared_identificado(self):
        modulo = carrega("switch-uplink-band")
        comandos = self.comando_de(modulo, "conexoes_tunel")
        self.assertTrue(comandos)
        for comando in comandos:
            self.afirma_agente_no_argv(comando, SONDA)


class IdentidadeHerdadaDaFonteUnica(unittest.TestCase):
    """`generate-legal-corpus-live-verification-20260812` não define UA próprio:
    ele usa o `NAVEGADOR` de `tools/generate-legal-corpus`, que é a fonte única
    daquele caminho. A guarda existe para o dia em que a fonte perder a chave —
    sem ela, a conferência sairia anônima para o gov.br sem ninguém notar."""

    def setUp(self):
        self.modulo = carrega("generate-legal-corpus-live-verification-20260812")

    def test_herda_o_ua_canonico_do_gerador_de_corpus(self):
        glc = carrega("generate-legal-corpus")
        cabecalhos = self.modulo.cabecalhos_de_saida(glc)
        self.assertRegex(cabecalhos["User-Agent"], CANONICO)

    def test_para_o_programa_se_a_fonte_unica_perder_a_identidade(self):
        class FonteSemIdentidade:
            NAVEGADOR = {"Accept-Language": "pt-BR"}

        with self.assertRaises(SystemExit) as capturado:
            self.modulo.cabecalhos_de_saida(FonteSemIdentidade)
        self.assertIn("anonima", str(capturado.exception))


def _porta_livre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _ServidorDeMentira:
    """Servidor HTTP mínimo que só guarda o User-Agent de cada requisição."""

    def __init__(self):
        self.agentes = []
        agentes = self.agentes

        class Handler(http.server.BaseHTTPRequestHandler):
            def _responde(self):
                agentes.append(self.headers.get("User-Agent"))
                corpo = b"{}"
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(corpo)))
                self.end_headers()
                self.wfile.write(corpo)

            do_GET = _responde
            do_POST = _responde

            def log_message(self, *_):  # silencia o log do servidor de teste
                pass

        self.porta = _porta_livre()
        self.httpd = http.server.HTTPServer(("127.0.0.1", self.porta), Handler)

    def __enter__(self):
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=5)
        return False


class SondasEmShell(unittest.TestCase):
    """Prova de fio: o `-A` do curl chegou ao servidor, ou não chegou.

    Ler o script e ver a opção não prova nada — a opção pode estar depois do
    `--` ou numa chamada que não é a que executa. Aqui o servidor RECEBE.
    """

    def roda(self, ferramenta, ambiente, timeout=60):
        env = dict(os.environ)
        env.update(ambiente)
        return subprocess.run([str(RAIZ / "tools" / ferramenta)],
                              cwd=str(RAIZ), env=env, capture_output=True,
                              text=True, timeout=timeout)

    def test_check_oracle_liveness_sonda_o_languagetool_identificado(self):
        with _ServidorDeMentira() as servidor:
            endpoint = "http://127.0.0.1:%d/v2/check" % servidor.porta
            self.roda("check-oracle-liveness",
                      {"WIKI_LANGUAGETOOL_ENDPOINT": endpoint})
            agentes = list(servidor.agentes)
        self.assertTrue(agentes, "a ferramenta não chegou a requisitar o endpoint")
        for agente in agentes:
            self.assertEqual(
                agente, SONDA,
                "sonda anônima: até 2026-09-10 esta chamada saía como curl/8.x")

    def test_install_vnu_validator_baixa_como_wikijuridicabot(self):
        """Download de ferramenta sai para github.com. O servidor de mentira
        devolve dois bytes, a validação do .jar reprova em seguida e o script
        sai != 0 — o que este teste lê é o User-Agent que chegou ao fio."""
        # O script deriva o cache de `dirname($0)/..`, e o .jar real já está no
        # cache do repositório — rodá-lo daqui sairia por "already installed"
        # sem baixar nada. Uma cópia num diretório temporário com a mesma
        # estrutura (`<tmp>/tools/`) dá a ele um cache vazio, sem knob novo na
        # ferramenta e sem tocar o cache de verdade.
        with tempfile.TemporaryDirectory() as tmp:
            destino = pathlib.Path(tmp) / "tools"
            destino.mkdir()
            copia = destino / "install-vnu-validator"
            shutil.copy2(RAIZ / "tools" / "install-vnu-validator", copia)
            with _ServidorDeMentira() as servidor:
                ambiente = dict(os.environ)
                ambiente["VNU_VALIDATOR_URL"] = (
                    "http://127.0.0.1:%d/vnu.jar" % servidor.porta)
                subprocess.run([str(copia)], cwd=tmp, env=ambiente,
                               capture_output=True, text=True, timeout=60)
                agentes = list(servidor.agentes)
        self.assertTrue(agentes, "a ferramenta não chegou a baixar nada")
        for agente in agentes:
            self.assertRegex(agente, CANONICO)
            self.assertTrue(agente.endswith("; instalacao-de-ferramenta)"), agente)

    def test_regenerate_languagetool_evidence_sonda_identificada(self):
        """Só a PRIMEIRA requisição interessa: a conferência de disponibilidade.

        A ferramenta é um regenerador de evidência que roda por dezenas de
        minutos depois desse passo, e teste que espera isso não é teste — é
        pauta de madrugada. Então o processo é INTERROMPIDO assim que o
        servidor de mentira registra a requisição, pelo grupo de processos
        (o script chama `curl` e `python3` filhos, e matar só o pai deixaria
        órfão rodando contra um servidor que vai sumir).
        """
        endpoint_visto = None
        with tempfile.TemporaryDirectory() as tmp, _ServidorDeMentira() as servidor:
            endpoint = "http://127.0.0.1:%d/v2/check" % servidor.porta
            ambiente = dict(os.environ)
            ambiente.update({"LT_ENDPOINT": endpoint, "LT_REGISTROS": "1",
                             "LT_CONCORRENCIA": "1"})
            # A CÓPIA EM TMP NÃO É CAPRICHO. Rodada na raiz do repositório, esta
            # ferramenta anexa a `data/ops/languagetool_quality_evidence.jsonl`
            # (caminho RELATIVO) e dispara
            # `./tools/run-generate-supervised ./cmd/generate-languagetool-quality`
            # — um build Go de vários minutos. Um teste que corre contra o
            # relógio para matar o processo antes disso é um teste que um dia
            # perde a corrida, e `run-qualidade-diaria` o roda toda noite. Com a
            # cópia num `<tmp>/tools/`, os dois caminhos relativos resolvem
            # dentro do temporário: nada de produção é tocado nem construído.
            destino = pathlib.Path(tmp) / "tools"
            destino.mkdir()
            copia = destino / "regenerate-languagetool-evidence"
            shutil.copy2(RAIZ / "tools" / "regenerate-languagetool-evidence", copia)
            processo = subprocess.Popen(
                [str(copia)], cwd=tmp, env=ambiente, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, start_new_session=True)
            try:
                limite = time.monotonic() + 30
                while time.monotonic() < limite:
                    if servidor.agentes or processo.poll() is not None:
                        break
                    time.sleep(0.1)
                endpoint_visto = list(servidor.agentes)
            finally:
                if processo.poll() is None:
                    os.killpg(os.getpgid(processo.pid), signal.SIGTERM)
                try:
                    processo.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    os.killpg(os.getpgid(processo.pid), signal.SIGKILL)
                    processo.wait(timeout=15)
        self.assertTrue(endpoint_visto, "a ferramenta não chegou a requisitar o endpoint")
        self.assertEqual(endpoint_visto[0], SONDA)


if __name__ == "__main__":
    unittest.main(verbosity=2)
