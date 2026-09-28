#!/usr/bin/env python3
"""Prova que o vigia do uplink NAO derruba a rede de uma maquina cabeada.

────────────────────────────────────────────────────────────────────────────
O DEFEITO, e por que a leitura intuitiva dele estava errada

Ate 2026-09-22, `medir_wifi` (tools/check-network-health) fundia dois mundos
numa condicao so:

    rc, saida, _ = rodar([IW, "dev", interface, "link"])
    if rc != 0 or "Not connected" in saida:
        dados["associado"] = False
        return dados

A leitura natural — "numa placa cabeada o `iw` falha, entao basta separar o
rc" — e FALSA, e foi medida nesta maquina em 2026-09-22 (kernel 6.1, iw 5.19):

    iw dev lo         link -> rc 0   "Not connected."
    iw dev virbr0     link -> rc 0   "Not connected."
    iw dev wlp2s0     link -> rc 0   "Connected to e4:c0:e2:db:1d:45"
    iw dev naoexiste0 link -> rc 237 "command failed: No such device (-19)"

Numa interface que NAO e radio o `iw link` devolve rc 0 e a MESMA string de um
radio de verdade desassociado. O rc so vira != 0 quando a interface nao existe.
Por isso o caso que mata o mutante aqui e sempre `rc == 0` + "Not connected." —
e um conserto que apenas separasse o rc continuaria com o bug inteiro.

Quem separa os dois mundos e o kernel, pelo sysfs: `phy80211` (criado pelo
cfg80211 ao registrar o netdev, para exatamente os netdevs que o nl80211 sabe
enderecar) e `wireless/`. Ambos nascem no REGISTRO da interface, nunca na
associacao — e e isso que preserva a deteccao de radio caido de verdade.

────────────────────────────────────────────────────────────────────────────
POR QUE METADE DESTE ARQUIVO TESTA A FIACAO, E NAO A FUNCAO

O dicionario devolvido por `medir_wifi` nao faz mal a ninguem sozinho. O que
executa `nmcli device disconnect` na interface do uplink e o VEREDITO montado
a partir dele, tres elos adiante:

    check-network-health:406  avaliar() casa `wifi.get("associado") is False`
                              e emite a critica "radio nao associado a nenhum
                              BSS" no dominio "uplink"
    check-network-health:671  `curavel` = critica de dominio "uplink" -> True
    check-network-health:686  --repair + ciclos_ruins >= 2 sobe a escada
    check-network-health:562  degrau 0: `nmcli connection up` no perfil ativo
    check-network-health:565  degrau 1: `nmcli device disconnect <interface>`

A unit de producao passa `--repair` (ops/systemd/wikijuridica-network-health
.service) e o timer dispara a cada 60 s. Licao medida neste repositorio: o
mutante sobrevive no ponto de chamada. Por isso `MainNaoCuraMaquinaCabeada`
roda o `main()` INTEIRO, com o estado pre-carregado em `ciclos_ruins: 1` — de
modo que a unica coisa entre a execucao e o `nmcli device disconnect` e o
veredito sobre a interface cabeada.

Nada aqui toca a rede, o disco do repositorio ou a producao: `SYSFS_NET`,
`ESTADO`, `HISTORICO` e `TRAVA` apontam para um diretorio temporario, e toda
sonda externa (`rodar`, `medir_ping`, `medir_dns`, `avisar`) e substituida.
"""

import importlib.machinery
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr

RAIZ = os.environ.get("WIKI_ROOT", "/opt/wiki")

# Saida literal de `iw dev wlp2s0 link` capturada nesta maquina em 2026-09-22.
# Fixture copiada da fonte primaria, e nao escrita de memoria: o parser de
# medir_wifi e um punhado de regexes, e regex se testa contra o texto real.
LINK_ASSOCIADO = """Connected to e4:c0:e2:db:1d:45 (on wlp2s0)
\tSSID: MURILO 5G
\tfreq: 5180
\tRX: 1248133728 bytes (1641021 packets)
\tTX: 2901520415 bytes (3103813 packets)
\tsignal: -39 dBm
\trx bitrate: 433.3 MBit/s VHT-MCS 9 80MHz short GI VHT-NSS 1
\ttx bitrate: 433.3 MBit/s VHT-MCS 9 80MHz short GI VHT-NSS 1

\tbss flags:\tshort-slot-time
\tdtim period:\t1
\tbeacon int:\t100
"""

# Saida literal de `iw dev virbr0 link` e de `iw dev lo link` na mesma medicao:
# rc 0. E o caso central deste arquivo.
LINK_NAO_CONECTADO = "Not connected.\n"

INFO_ASSOCIADO = (
    "Interface wlp2s0\n\tifindex 3\n\twdev 0x1\n\ttype managed\n"
    "\tchannel 36 (5180 MHz), width: 80 MHz, center1: 5210 MHz\n")

STATION_ASSOCIADO = (
    "Station e4:c0:e2:db:1d:45 (on wlp2s0)\n"
    "\tconnected time:\t46999 seconds\n"
    "\ttx packets:\t3098674\n"
    "\ttx retries:\t26560\n"
    "\ttx failed:\t0\n"
    "\tbeacon loss:\t0\n")


def carrega(nome, ferramenta):
    """Carrega ferramenta SEM extensao .py, pelo caminho explicito.

    Mesmo idioma de tools/test_tres_estados_de_medidor.py:47, e pelo mesmo
    motivo: evita o `sys.path.insert` + import que obrigaria a um `# noqa: E402`,
    e suprimir o diagnostico em vez de resolver a causa e proibido aqui.
    """
    caminho = os.path.join(RAIZ, "tools", ferramenta)
    carregador = importlib.machinery.SourceFileLoader(nome, caminho)
    spec = importlib.util.spec_from_loader(nome, carregador)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


class SysfsDeMentira:
    """Um /sys/class/net de fixture. Aponta a CONSTANTE do modulo, em vez de
    substituir o predicado: teste que reimplementa a regra fica verde com a
    regra desligada no codigo real."""

    def __init__(self, modulo):
        self.modulo = modulo
        self.original = modulo.SYSFS_NET
        self.raiz = tempfile.mkdtemp(prefix="sysfs-net-")
        modulo.SYSFS_NET = self.raiz

    def cria(self, interface, radio, marca="wireless"):
        base = os.path.join(self.raiz, interface)
        os.makedirs(base, exist_ok=True)
        if radio:
            if marca == "wireless":
                os.makedirs(os.path.join(base, "wireless"), exist_ok=True)
            else:
                # phy80211 e um LINK SIMBOLICO no sysfs real; o alvo nem precisa
                # existir, e o predicado usa os.path.exists, que segue o link.
                destino = os.path.join(self.raiz, "phy0")
                os.makedirs(destino, exist_ok=True)
                enlace = os.path.join(base, "phy80211")
                if not os.path.lexists(enlace):
                    os.symlink(destino, enlace)
        return interface

    def encerra(self):
        self.modulo.SYSFS_NET = self.original
        shutil.rmtree(self.raiz, ignore_errors=True)


def rodar_de_mentira(respostas, padrao=(0, "", "")):
    """Devolve um substituto de `rodar` guiado pelo comando recebido."""

    def substituto(comando, timeout=25):
        chave = " ".join(comando)
        for fragmento, resposta in respostas.items():
            if fragmento in chave:
                return resposta
        return padrao

    return substituto


class MedirWifiSeparaOsTresCasos(unittest.TestCase):
    """A funcao: tres mundos, tres respostas."""

    def setUp(self):
        self.m = carrega("nh_wifi", "check-network-health")
        self.sysfs = SysfsDeMentira(self.m)
        self.addCleanup(self.sysfs.encerra)

    # (a) — O CASO QUE MATA O MUTANTE.
    def test_interface_cabeada_devolve_dicionario_vazio(self):
        self.sysfs.cria("enp3s0", radio=False)
        # rc 0 e "Not connected.", que e o que o `iw` 5.19 devolve numa
        # interface nao-radio. Um conserto que so olhasse o rc passaria batido.
        self.m.rodar = rodar_de_mentira({"link": (0, LINK_NAO_CONECTADO, "")})
        self.assertEqual(
            self.m.medir_wifi("enp3s0"), {},
            "interface sem radio TEM de devolver {}, como a docstring promete: "
            "qualquer chave aqui e truthy em avaliar() e reabre a cadeia que "
            "termina em `nmcli device disconnect`")

    def test_interface_cabeada_nem_chama_o_iw(self):
        """O `iw` nem precisa estar instalado na maquina nova."""
        self.sysfs.cria("enp3s0", radio=False)
        chamadas = []

        def registra(comando, timeout=25):
            chamadas.append(comando)
            return (0, LINK_NAO_CONECTADO, "")

        self.m.rodar = registra
        self.assertEqual(self.m.medir_wifi("enp3s0"), {})
        self.assertEqual(chamadas, [],
                         "numa interface nao-radio o vigia nao deve sequer "
                         "invocar o `iw`")

    # (b) — POSITIVO: radio de verdade caido continua sendo detectado.
    def test_radio_sem_associacao_continua_acusando(self):
        self.sysfs.cria("wlp2s0", radio=True, marca="wireless")
        self.m.rodar = rodar_de_mentira({"link": (0, LINK_NAO_CONECTADO, "")})
        self.assertEqual(
            self.m.medir_wifi("wlp2s0"), {"associado": False},
            "radio de verdade sem BSS TEM de continuar devolvendo "
            "{'associado': False} — e ele que detecta radio caido na maquina "
            "velha, que e WiFi 5 GHz e serve producao")

    def test_phy80211_tambem_marca_radio(self):
        """Segunda evidencia de radio: o driver pode expor uma marca e nao a
        outra, e perder o radio aqui seria perder o vigia inteiro."""
        self.sysfs.cria("wlx00", radio=True, marca="phy80211")
        self.m.rodar = rodar_de_mentira({"link": (0, LINK_NAO_CONECTADO, "")})
        self.assertEqual(self.m.medir_wifi("wlx00"), {"associado": False})

    # (c) — radio associado: nenhum campo pode ter sumido.
    def test_radio_associado_devolve_os_campos_de_sempre(self):
        self.sysfs.cria("wlp2s0", radio=True)
        self.m.rodar = rodar_de_mentira({
            "link": (0, LINK_ASSOCIADO, ""),
            "info": (0, INFO_ASSOCIADO, ""),
            "station dump": (0, STATION_ASSOCIADO, ""),
        })
        dados = self.m.medir_wifi("wlp2s0")
        self.assertEqual(dados["associado"], True)
        self.assertEqual(dados["ssid"], "MURILO 5G")
        self.assertEqual(dados["bssid"], "e4:c0:e2:db:1d:45")
        self.assertEqual(dados["freq_mhz"], 5180)
        self.assertEqual(dados["banda"], "5GHz")
        self.assertEqual(dados["sinal_dbm"], -39)
        self.assertEqual(dados["tx_bitrate_mbit"], 433.3)
        self.assertEqual(dados["rx_bitrate_mbit"], 433.3)
        self.assertEqual(dados["canal"], 36)
        self.assertEqual(dados["largura_mhz"], 80)
        self.assertEqual(dados["tx_retries"], 26560)
        self.assertEqual(dados["tempo_associado_s"], 46999)

    # (d) — radio presente, instrumento mudo: NAO MEDI, e nao veredito.
    def test_radio_com_iw_ausente_deixa_rastro_e_nao_acusa(self):
        self.sysfs.cria("wlp2s0", radio=True)
        self.m.rodar = rodar_de_mentira(
            {"link": (127, "", "[Errno 2] No such file or directory: '/usr/sbin/iw'")})
        dados = self.m.medir_wifi("wlp2s0")
        self.assertNotIn(
            "associado", dados,
            "`iw` ausente e falta de INSTRUMENTO, nao radio caido: com "
            "`associado: False` a escada de cura subiria sobre medicao cega")
        self.assertIn("nao_medido", dados,
                      "a falha do instrumento TEM de deixar rastro; o `{}` mudo "
                      "e o defeito que o FALHAS_SYSTEMD do check-portal-health "
                      "ja teve de consertar")
        self.assertIn("rc=127", dados["nao_medido"])

    # Controle NEGATIVO, e com ORACULO INDEPENDENTE.
    #
    # Todos os testes acima rodam contra o sysfs de FIXTURE. Se a marca de radio
    # mudasse de nome no kernel, eles seguiriam verdes e o vigia real ficaria
    # cego justamente na maquina WiFi que serve producao. Um controle que
    # recalculasse a lista de radios com a MESMA regra do predicado nao pegaria
    # isso — a renomeacao esvaziaria os dois lados e o teste passaria por
    # vacuidade. Por isso a verdade vem do `iw dev`, que pergunta ao nl80211:
    # outro caminho de leitura, e exatamente o caminho que o `iw link` usa para
    # medir. Se os dois discordarem, e o predicado que esta errado.
    def test_o_radio_real_desta_maquina_e_reconhecido(self):
        self.m.SYSFS_NET = self.sysfs.original
        rc, saida, _ = self.m.rodar([self.m.IW, "dev"])
        if rc != 0:
            self.skipTest(f"`iw` indisponivel (rc={rc}): sem oraculo independente")
        # O `iw dev` tambem lista "Unnamed/non-netdev interface" (P2P-device),
        # que nao tem linha `Interface <nome>` e nao existe em /sys/class/net.
        radios = re.findall(r"^\s*Interface\s+(\S+)\s*$", saida, re.MULTILINE)
        if not radios:
            self.skipTest("host sem radio: nada a confirmar contra o nl80211")
        for nome in radios:
            self.assertTrue(
                self.m.e_interface_de_radio(nome),
                f"o nl80211 lista {nome} como radio e o predicado, que le o "
                "sysfs, nao o reconheceu: o vigia ficaria cego na maquina que "
                "serve producao")
        for nome in os.listdir(self.m.SYSFS_NET):
            if nome in radios:
                continue
            self.assertFalse(
                self.m.e_interface_de_radio(nome),
                f"{nome} nao aparece no `iw dev` e o predicado disse que e "
                "radio: o vigia trataria uma interface cabeada como radio")


class MainNaoCuraMaquinaCabeada(unittest.TestCase):
    """A FIACAO: o que dispara `nmcli device disconnect` e o veredito, nao o
    dicionario. Aqui o `main()` roda inteiro contra um mundo cabeado."""

    def monta(self, radio, link=None):
        m = carrega("nh_main", "check-network-health")
        sysfs = SysfsDeMentira(m)
        self.addCleanup(sysfs.encerra)
        sysfs.cria("enp3s0", radio=radio)

        area = tempfile.mkdtemp(prefix="network-health-")
        self.addCleanup(shutil.rmtree, area, True)
        m.ESTADO = os.path.join(area, "estado.json")
        m.HISTORICO = os.path.join(area, "historico.jsonl")
        m.TRAVA = os.path.join(area, "trava")

        # ciclos_ruins ja em 1: com o +1 desta execucao bate o >= 2 de
        # check-network-health:686. Assim a UNICA coisa entre esta execucao e o
        # `nmcli device disconnect` e o veredito sobre a interface cabeada.
        with open(m.ESTADO, "w", encoding="utf-8") as arquivo:
            json.dump({"ciclos_ruins": 1, "degrau": 0, "curas": [],
                       "dominios_abertos": []}, arquivo)

        rota = json.dumps([{"dst": "default", "gateway": "192.168.1.1",
                            "dev": "enp3s0"}])
        m.rodar = rodar_de_mentira({
            "ip -j route show default": (0, rota, ""),
            "ip -V": (0, "ip utility, iproute2-6.1.0\n", ""),
            # A medicao de 2026-09-22: numa interface nao-radio o `iw` devolve
            # rc 0 e "Not connected.", igualzinho a um radio caido.
            "link": link or (0, LINK_NAO_CONECTADO, ""),
        })
        m.ler_contadores_interface = lambda interface: {}
        m.ler_tcp_snmp = lambda: {}
        m.medir_ping = lambda destino, pacotes=20, intervalo=0.2: {
            "destino": destino, "alcancavel": True, "enviados": pacotes,
            "recebidos": pacotes, "perda_pct": 0.0, "rtt_min_ms": 1.0,
            "rtt_medio_ms": 2.0, "rtt_max_ms": 4.0, "rtt_desvio_ms": 0.5}
        m.medir_dns = lambda nomes: [
            {"nome": n, "resolveu": True, "segundos": 0.01} for n in nomes]
        self.alertas = []
        m.avisar = lambda *a, **k: self.alertas.append(a) or True
        self.curas = []
        m.curar = lambda *a, **k: (self.curas.append(a), ("cura", 0, ""))[1]
        return m

    def roda(self, m):
        argv = sys.argv
        sys.argv = ["check-network-health", "--repair", "--banda-esperada", "5GHz"]
        self.erro = io.StringIO()
        try:
            with redirect_stderr(self.erro):
                rc = m.main()
        finally:
            sys.argv = argv
        with open(m.HISTORICO, encoding="utf-8") as arquivo:
            evento = json.loads(arquivo.read().strip().splitlines()[-1])
        return rc, evento

    def test_maquina_cabeada_nao_sobe_a_escada_de_cura(self):
        m = self.monta(radio=False)
        rc, evento = self.roda(m)
        self.assertEqual(
            self.curas, [],
            "o vigia tentou CURAR uma maquina cabeada: o degrau 1 e "
            "`nmcli device disconnect enp3s0`, isto e, o vigia derrubando o "
            "uplink que deveria vigiar")
        descricoes = [p["descricao"] for p in evento["problemas"]]
        self.assertNotIn("radio nao associado a nenhum BSS", descricoes,
                         f"critica de radio numa interface sem radio: {descricoes}")
        self.assertFalse(evento["curavel"],
                         f"interface cabeada classificada como curavel: {descricoes}")
        self.assertEqual(evento["wifi"], {})
        self.assertIsNone(evento["reparo"])
        self.assertEqual(rc, 0, f"veredito degradado sem defeito real: {descricoes}")
        # A flag --banda-esperada 5GHz da unit nao pode inventar alerta de banda
        # numa maquina que nao tem radio.
        self.assertNotIn("banda", {p["dominio"] for p in evento["problemas"]})

    def test_radio_caido_de_verdade_continua_subindo_a_escada(self):
        """Controle POSITIVO. Sem ele, o teste acima ficaria verde com o vigia
        desligado — e um vigia que nunca cura nao e conserto, e outra cegueira."""
        m = self.monta(radio=True)
        rc, evento = self.roda(m)
        descricoes = [p["descricao"] for p in evento["problemas"]]
        self.assertIn("radio nao associado a nenhum BSS", descricoes,
                      "radio de verdade sem BSS parou de ser detectado")
        self.assertTrue(evento["curavel"])
        self.assertEqual(len(self.curas), 1,
                         "radio caido TEM de subir a escada de cura")
        self.assertEqual(rc, 1)


class VigiaCegoSaiDois(unittest.TestCase):
    """RADIO PRESENTE + `iw` mudo = NAO MEDI (exit 2), e nao "esta tudo bem".

    A unit declara `SuccessExitStatus=0 1`: exit 0 e exit 1 sao Result=success.
    Entao um vigia que perde o `iw` e mesmo assim sai 0 fica CEGO E VERDE para
    sempre, e o `OnFailure=wikijuridica-alerta@%N.service` nunca alcanca o dono.
    Na maquina nova isso e mais provavel, nao menos: o `iw` entra pela lista de
    pacotes do provisionamento, e um pacote que fique de fora faz o vigia nascer
    cego.

    A ASSIMETRIA que estes testes travam: interface nao-radio NAO e "nao
    medido" — e "nao se aplica", devolve {} e continua saindo 0. So o radio
    cego vira 2.
    """

    monta = MainNaoCuraMaquinaCabeada.monta
    roda = MainNaoCuraMaquinaCabeada.roda

    # `iw` ausente: rodar() devolve 127 por OSError (check-network-health:134).
    IW_AUSENTE = (127, "", "[Errno 2] No such file or directory: '/usr/sbin/iw'")

    def test_radio_presente_com_iw_ausente_sai_2(self):
        m = self.monta(radio=True, link=self.IW_AUSENTE)
        rc, evento = self.roda(m)
        self.assertEqual(
            rc, 2,
            "radio presente e `iw` mudo TEM de sair 2: a unit mascara 0 e 1, "
            "entao com 0 o vigia fica cego e verde para sempre")
        self.assertIn("NAO MEDIDO:", self.erro.getvalue())
        self.assertIn("instrumento",
                      {p["dominio"] for p in evento["problemas"]})
        self.assertIn("rede-instrumento", [a[0] for a in self.alertas],
                      "o dono TEM de ser alertado de que o vigia cegou")

    def test_radio_cego_nao_sobe_a_escada_de_cura(self):
        """Medicao cega nunca autoriza cura — a mesma doutrina da guarda do
        `ip -V`. O dominio e "instrumento", e `curavel` exige "uplink"."""
        m = self.monta(radio=True, link=self.IW_AUSENTE)
        _, evento = self.roda(m)
        self.assertEqual(self.curas, [],
                         "a escada de cura subiu sobre medicao cega")
        self.assertFalse(evento["curavel"])

    def test_radio_cego_nao_joga_fora_rota_ping_tcp_e_dns(self):
        """O exit 2 do `iw` decide-se no FIM, nao aborta na hora.

        Sem o `ip` a medicao inteira colapsa e sair cedo e correto. Sem o `iw`
        colapsa APENAS o radio: rota, ping, TCP e DNS continuam mensuraveis, e
        aborta-los trocaria um ponto cego por quatro.
        """
        m = self.monta(radio=True, link=self.IW_AUSENTE)
        rc, evento = self.roda(m)
        self.assertEqual(rc, 2)
        self.assertTrue(evento["rota_default"])
        self.assertEqual(evento["ping_gateway"]["perda_pct"], 0.0)
        self.assertTrue(evento["dns"], "o DNS ficou sem medir por causa do `iw`")
        self.assertIn("ping_externo", evento)
        self.assertIn("nao_medido", evento["wifi"])

    # A ASSIMETRIA, nos dois sentidos.
    def test_maquina_cabeada_sem_iw_continua_saindo_0(self):
        m = self.monta(radio=False, link=self.IW_AUSENTE)
        rc, evento = self.roda(m)
        self.assertEqual(
            rc, 0,
            "interface nao-radio nao e 'nao medido', e 'nao se aplica': a "
            "maquina cabeada nao pode alertar o dono a cada 60 s por nao ter "
            "um radio que ela nunca teve")
        self.assertEqual(evento["wifi"], {})
        self.assertNotIn("instrumento",
                         {p["dominio"] for p in evento["problemas"]})
        self.assertNotIn("NAO MEDIDO:", self.erro.getvalue())

    def test_radio_associado_de_verdade_continua_saindo_0(self):
        """Controle de nao-regressao: o caminho feliz da maquina que serve
        producao hoje nao pode ter virado 2."""
        m = self.monta(radio=True, link=(0, LINK_ASSOCIADO, ""))
        rc, evento = self.roda(m)
        self.assertEqual(rc, 0, f"problemas: {evento['problemas']}")
        self.assertTrue(evento["wifi"]["associado"])
        self.assertEqual(evento["wifi"]["ssid"], "MURILO 5G")
        self.assertNotIn("nao_medido", evento["wifi"])
        self.assertNotIn("instrumento",
                         {p["dominio"] for p in evento["problemas"]})

    def test_radio_caido_de_verdade_continua_saindo_1_e_curando(self):
        """O 2 nao pode ter comido o 1: radio desassociado e VEREDITO."""
        m = self.monta(radio=True, link=(0, LINK_NAO_CONECTADO, ""))
        rc, evento = self.roda(m)
        self.assertEqual(rc, 1, "radio caido e veredito (1), nao defeito (2)")
        self.assertIn("uplink", {p["dominio"] for p in evento["problemas"]})
        self.assertEqual(len(self.curas), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
