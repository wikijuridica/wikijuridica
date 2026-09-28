#!/usr/bin/env python3
"""Prova que o vigia do uplink ENXERGA o enlace cabeado e nao o cura as cegas.

────────────────────────────────────────────────────────────────────────────
O DEFEITO (2026-09-24, maquina nova: RTL8125B/r8169 na porta 2.5G de um
roteador Sagemcom, plano de 1 Gbit/s)

O enlace passou mais de uma hora em 100 Mbit/s. O kernel registrou, varias
vezes, "Downshift occurred from negotiated speed 2.5Gbps to actual speed
100Mbps, check cabling!", e o dono so descobriu por teste de velocidade. O
vigia rodou a cada 60 s o tempo todo, imprimindo

    enp10s0 - ch- - Mbit/s - dBm | gw perda 0.0% ...

e saindo 0: `medir_wifi` devolve {} para interface nao-radio — e TEM de
devolver, ver tools/test_medir_wifi_nao_derruba_maquina_cabeada.py —, e nada
mais olhava a camada fisica. Na mesma noite, as 20:13:08, sem rota default, a
escada de cura chamou `nmcli device disconnect None` e o vigia caiu com
TypeError: a cura nao foi gravada e o teto de curas/hora furou.

O QUE ESTE ARQUIVO TRAVA

  1. medir_enlace_cabeado le velocidade/duplex/portadora do sysfs so para
     placa FISICA nao-radio (tem `device`), e nunca inventa velocidade.
  2. Velocidade abaixo de --velocidade-minima-mbit vira ALERTA no dominio
     "enlace" — nunca cura: nenhum degrau da escada renegocia uma PHY, e oito
     intervencoes no servidor naquela noite cairam todas de volta em 100.
  3. Quedas de portadora viram alerta pelo DELTA de carrier_changes, e o
     contador zerado por recarga do driver nao vira queda.
  4. Sem rota default: a placa continua medida (ultima interface conhecida),
     cobre sem portadora nao sobe a escada, e a cura nunca recebe None.

Nada aqui toca a rede nem o estado de producao: SYSFS_NET, ESTADO, HISTORICO e
TRAVA apontam para diretorio temporario, e toda sonda externa e substituida.
"""

import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from tools.test_medir_wifi_nao_derruba_maquina_cabeada import (
    LINK_NAO_CONECTADO, carrega, rodar_de_mentira)


def cria_placa(raiz, interface, fisica=True, radio=False, **atributos):
    """Um /sys/class/net/<if> de fixture. `device` e o que o kernel cria para
    placa fisica (PCI/USB) e nao cria para bridge, veth e tunel; atributo
    ausente reproduz o EINVAL que o kernel devolve a `speed` sem portadora."""
    base = os.path.join(raiz, interface)
    os.makedirs(base, exist_ok=True)
    if fisica:
        os.makedirs(os.path.join(base, "device"), exist_ok=True)
    if radio:
        os.makedirs(os.path.join(base, "wireless"), exist_ok=True)
    for nome, valor in atributos.items():
        with open(os.path.join(base, nome), "w", encoding="utf-8") as arquivo:
            arquivo.write(f"{valor}\n")
    return base


def placa_saudavel(velocidade=2500, carrier_changes=6):
    return {"speed": velocidade, "duplex": "full", "carrier": 1,
            "carrier_changes": carrier_changes, "operstate": "up"}


class MedirEnlaceCabeado(unittest.TestCase):
    """A funcao: placa fisica, placa virtual, radio e cobre sem portadora."""

    def setUp(self):
        self.m = carrega("nh_enlace", "check-network-health")
        self.raiz = tempfile.mkdtemp(prefix="sysfs-net-")
        self.addCleanup(shutil.rmtree, self.raiz, True)
        self.original = self.m.SYSFS_NET
        self.m.SYSFS_NET = self.raiz

    def test_placa_em_100_devolve_a_velocidade_negociada(self):
        cria_placa(self.raiz, "enp10s0", **placa_saudavel(velocidade=100))
        self.assertEqual(
            self.m.medir_enlace_cabeado("enp10s0"),
            {"velocidade_mbit": 100, "duplex": "full", "carrier": 1,
             "carrier_changes": 6, "operstate": "up"})

    def test_bridge_sem_device_nao_se_aplica(self):
        cria_placa(self.raiz, "virbr0", fisica=False, **placa_saudavel(velocidade=10))
        self.assertEqual(self.m.medir_enlace_cabeado("virbr0"), {},
                         "bridge nao e enlace de cobre: medir aqui acusaria "
                         "'10 Mbit/s' numa interface virtual")

    def test_radio_nao_e_enlace_cabeado(self):
        """Placa WiFi tambem tem `device`; quem a mede e medir_wifi."""
        cria_placa(self.raiz, "wlp2s0", radio=True, **placa_saudavel(velocidade=433))
        self.assertEqual(self.m.medir_enlace_cabeado("wlp2s0"), {})

    def test_sem_portadora_nao_inventa_velocidade(self):
        cria_placa(self.raiz, "enp10s0", carrier=0, carrier_changes=7,
                   operstate="down")
        dados = self.m.medir_enlace_cabeado("enp10s0")
        self.assertEqual(dados["carrier"], 0)
        self.assertNotIn("velocidade_mbit", dados,
                         "sem portadora o kernel nao da velocidade: numero aqui "
                         "seria inventado")

    def test_velocidade_desconhecida_fica_ausente(self):
        cria_placa(self.raiz, "enp10s0", **placa_saudavel(velocidade=-1))
        self.assertNotIn("velocidade_mbit", self.m.medir_enlace_cabeado("enp10s0"),
                         "-1 e 'desconhecida' no sysfs, nao velocidade medida")

    # Controle com ORACULO INDEPENDENTE sobre a maquina real. O sysfs e o
    # `ethtool` leem a mesma PHY por caminhos diferentes (atributo do netdev
    # contra ETHTOOL_MSG_LINKMODES_GET no netlink). Se o atributo mudasse de
    # nome ou de unidade, os testes de fixture seguiriam verdes e o vigia real
    # ficaria cego de novo.
    def test_a_placa_real_desta_maquina_bate_com_o_ethtool(self):
        self.m.SYSFS_NET = self.original
        conferidas = 0
        for nome in sorted(os.listdir(self.original)):
            dados = self.m.medir_enlace_cabeado(nome)
            if dados.get("carrier") != 1 or "velocidade_mbit" not in dados:
                continue
            rc, saida, _ = self.m.rodar(["ethtool", nome])
            achado = re.search(r"Speed:\s*(\d+)Mb/s", saida)
            if rc != 0 or not achado:
                continue
            conferidas += 1
            self.assertEqual(dados["velocidade_mbit"], int(achado.group(1)),
                             f"sysfs e ethtool discordam em {nome}")
        if not conferidas:
            self.skipTest("nenhuma placa cabeada com portadora e ethtool legivel")


class MainEnxergaEnlaceCabeado(unittest.TestCase):
    """A FIACAO: o `main()` inteiro contra um mundo cabeado, com a unit de
    producao em mente (`--repair` e ciclos_ruins ja em 1, de modo que so o
    veredito separa a execucao da escada de cura)."""

    def monta(self, placa, rota=True, estado_extra=None):
        m = carrega("nh_enlace_main", "check-network-health")
        raiz = tempfile.mkdtemp(prefix="sysfs-net-")
        self.addCleanup(shutil.rmtree, raiz, True)
        m.SYSFS_NET = raiz
        cria_placa(raiz, "enp10s0", **placa)

        area = tempfile.mkdtemp(prefix="network-health-")
        self.addCleanup(shutil.rmtree, area, True)
        m.ESTADO = os.path.join(area, "estado.json")
        m.HISTORICO = os.path.join(area, "historico.jsonl")
        m.TRAVA = os.path.join(area, "trava")
        estado = {"ciclos_ruins": 1, "degrau": 0, "curas": [], "dominios_abertos": []}
        estado.update(estado_extra or {})
        with open(m.ESTADO, "w", encoding="utf-8") as arquivo:
            json.dump(estado, arquivo)

        rotas = [{"dst": "default", "gateway": "192.168.1.1", "dev": "enp10s0"}] if rota else []
        m.rodar = rodar_de_mentira({
            "ip -j route show default": (0, json.dumps(rotas), ""),
            "ip route show default": (0, "", ""),
            "ip -V": (0, "ip utility, iproute2-6.1.0\n", ""),
            "link": (0, LINK_NAO_CONECTADO, ""),
        })
        m.ler_contadores_interface = lambda interface: {}
        m.ler_tcp_snmp = lambda: {}
        m.medir_ping = lambda destino, pacotes=20, intervalo=0.2: {
            "destino": destino, "alcancavel": True, "enviados": pacotes,
            "recebidos": pacotes, "perda_pct": 0.0, "rtt_min_ms": 0.5,
            "rtt_medio_ms": 0.6, "rtt_max_ms": 0.8, "rtt_desvio_ms": 0.1}
        m.medir_dns = lambda nomes: [
            {"nome": n, "resolveu": True, "segundos": 0.01} for n in nomes]
        self.alertas = []
        m.avisar = lambda *a, **k: self.alertas.append((a, k)) or True
        self.curas = []
        m.curar = lambda *a, **k: (self.curas.append(a), ("cura", 0, ""))[1]
        return m

    def roda(self, m, minimo="1000"):
        argv = sys.argv
        sys.argv = ["check-network-health", "--repair", "--banda-esperada", "5GHz"]
        if minimo is not None:
            sys.argv += ["--velocidade-minima-mbit", minimo]
        self.saida = io.StringIO()
        try:
            with redirect_stderr(io.StringIO()), redirect_stdout(self.saida):
                rc = m.main()
        finally:
            sys.argv = argv
        with open(m.HISTORICO, encoding="utf-8") as arquivo:
            evento = json.loads(arquivo.read().strip().splitlines()[-1])
        return rc, evento

    def dominios(self, evento):
        return {p["dominio"] for p in evento["problemas"]}

    # (a) O CASO DA NOITE DE 2026-09-24.
    def test_enlace_em_100_alerta_no_dominio_enlace_e_nao_cura(self):
        m = self.monta(placa_saudavel(velocidade=100))
        rc, evento = self.roda(m)
        enlace = [p for p in evento["problemas"] if p["dominio"] == "enlace"]
        self.assertEqual(len(enlace), 1, f"problemas: {evento['problemas']}")
        self.assertEqual(enlace[0]["severidade"], "alta")
        self.assertIn("100 Mbit/s", enlace[0]["descricao"])
        self.assertEqual(rc, 1, "enlace abaixo do minimo e VEREDITO degradado (1)")
        self.assertEqual(self.curas, [],
                         "nenhum degrau da escada renegocia PHY: curar aqui so "
                         "somaria um corte ao enlace ja degradado")
        self.assertFalse(evento["curavel"])
        chaves = [a[0] for a, _ in self.alertas]
        self.assertIn("rede-enlace", chaves, "o dono TEM de saber da queda para 100")
        evidencia = [a[4] for a, _ in self.alertas if a[0] == "rede-enlace"][0]
        self.assertIn("speed -> 100 Mbit/s", evidencia)
        self.assertNotIn("dBm", evidencia,
                         "evidencia de radio num alerta de cabo e evidencia vazia")
        self.assertIn("enp10s0 cabo 100 Mbit/s", self.saida.getvalue())

    # (b) CONTROLES NEGATIVOS: sem falso alarme.
    def test_enlace_em_2500_nao_alerta(self):
        m = self.monta(placa_saudavel(velocidade=2500))
        rc, evento = self.roda(m)
        self.assertEqual(rc, 0, f"problemas: {evento['problemas']}")
        self.assertNotIn("enlace", self.dominios(evento))
        self.assertEqual(self.alertas, [])

    def test_enlace_em_1000_com_minimo_1000_nao_alerta(self):
        """O plano e de 1 Gbit/s: downshift de 2.5G para 1G nao custa nada."""
        m = self.monta(placa_saudavel(velocidade=1000))
        rc, evento = self.roda(m)
        self.assertEqual(rc, 0, f"problemas: {evento['problemas']}")
        self.assertNotIn("enlace", self.dominios(evento))

    def test_sem_a_flag_a_velocidade_nao_e_conferida(self):
        """Default 0: host cuja placa so faz 100 nao alerta a cada 60 s."""
        m = self.monta(placa_saudavel(velocidade=100))
        rc, evento = self.roda(m, minimo=None)
        self.assertEqual(rc, 0, f"problemas: {evento['problemas']}")
        self.assertNotIn("enlace", self.dominios(evento))
        self.assertEqual(evento["enlace"]["velocidade_mbit"], 100,
                         "sem a flag o vigia continua MEDINDO; so nao julga")

    # (c) QUEDAS DE PORTADORA, sempre como delta.
    def anterior(self, carrier_changes):
        return {"ultima_medicao": {
            "medido_em": "2026-09-24T23:00:00+00:00",
            "enlace_interface": "enp10s0",
            "enlace": placa_saudavel(carrier_changes=carrier_changes)}}

    def test_rajada_de_quedas_vira_alta(self):
        m = self.monta(placa_saudavel(carrier_changes=16),
                       estado_extra=self.anterior(10))
        rc, evento = self.roda(m)
        self.assertEqual(evento["delta"]["d_carrier_changes"], 6)
        quedas = [p for p in evento["problemas"] if "caiu" in p["descricao"]]
        self.assertEqual(len(quedas), 1)
        self.assertEqual(quedas[0]["severidade"], "alta")
        self.assertIn("caiu 3x", quedas[0]["descricao"])
        self.assertEqual(rc, 1)
        self.assertEqual(self.curas, [])

    def test_uma_queda_avisa_como_media_e_nao_degrada(self):
        m = self.monta(placa_saudavel(carrier_changes=12),
                       estado_extra=self.anterior(10))
        rc, evento = self.roda(m)
        quedas = [p for p in evento["problemas"] if "caiu" in p["descricao"]]
        self.assertEqual([q["severidade"] for q in quedas], ["media"])
        self.assertEqual(rc, 0, "queda isolada (roteador reiniciando) nao e degradacao")

    def test_contador_zerado_pela_recarga_do_driver_nao_vira_queda(self):
        m = self.monta(placa_saudavel(carrier_changes=2),
                       estado_extra=self.anterior(10))
        rc, evento = self.roda(m)
        self.assertNotIn("d_carrier_changes", evento["delta"])
        self.assertTrue(evento["delta"].get("contadores_zerados"))
        self.assertNotIn("enlace", self.dominios(evento))
        self.assertEqual(rc, 0)

    # (d) SEM ROTA DEFAULT: o caso das 20:13:08.
    def test_sem_rota_e_sem_portadora_mede_a_placa_e_nao_sobe_a_escada(self):
        m = self.monta({"carrier": 0, "carrier_changes": 7, "operstate": "down"},
                       rota=False, estado_extra=self.anterior(6))
        rc, evento = self.roda(m)
        self.assertEqual(evento["enlace_interface"], "enp10s0",
                         "sem rota a placa some do vigia: e justamente quando o "
                         "cobre caiu que medi-la importa")
        descricoes = " | ".join(p["descricao"] for p in evento["problemas"])
        self.assertIn("sem rota default", descricoes)
        self.assertIn("sem portadora", descricoes)
        self.assertFalse(evento["curavel"],
                         "nenhum degrau devolve portadora; subir a escada so gasta "
                         "o teto de curas/hora")
        self.assertEqual(self.curas, [])
        self.assertEqual(rc, 1)

    def test_sem_rota_com_portadora_cura_a_ultima_interface_conhecida(self):
        """Portadora presente e rota ausente (DHCP empacado): a escada sobe, e
        sobre a placa conhecida — nunca sobre None."""
        m = self.monta(placa_saudavel(), rota=False, estado_extra=self.anterior(6))
        rc, evento = self.roda(m)
        self.assertTrue(evento["curavel"])
        self.assertEqual(len(self.curas), 1)
        self.assertEqual(self.curas[0][1], "enp10s0",
                         f"a cura recebeu {self.curas[0][1]!r} como interface")
        self.assertEqual(rc, 1)

    # (e) "NORMALIZADO" fala do cabo, e nao "? a ? Mbit/s".
    def test_normalizado_de_maquina_cabeada_descreve_o_cabo(self):
        m = self.monta(placa_saudavel(velocidade=2500),
                       estado_extra={"dominios_abertos": ["rede-enlace"]})
        rc, _ = self.roda(m)
        self.assertEqual(rc, 0)
        resolvidos = [a for a, k in self.alertas if k.get("resolvido")]
        self.assertEqual(len(resolvidos), 1)
        self.assertEqual(resolvidos[0][0], "rede-enlace")
        self.assertIn("cabo 2500 Mbit/s full", resolvidos[0][3])


class CurarSemInterfaceNaoCai(unittest.TestCase):
    """O degrau que endereca a interface nunca monta argv com None."""

    def test_reconectar_sem_interface_devolve_rc_1_sem_type_error(self):
        m = carrega("nh_curar", "check-network-health")
        chamadas = []
        m.rodar = lambda comando, timeout=25: (chamadas.append(comando), (0, "", ""))[1]
        degrau = m.DEGRAUS.index("reconectar-dispositivo")
        nome, rc, detalhe = m.curar(degrau, None, None)
        self.assertEqual((nome, rc), ("reconectar-dispositivo", 1))
        self.assertIn("sem interface", detalhe)
        self.assertEqual(chamadas, [], "nenhum nmcli pode sair com argv None")

    def test_reiniciar_networkmanager_nao_depende_de_interface(self):
        m = carrega("nh_curar2", "check-network-health")
        chamadas = []
        m.rodar = lambda comando, timeout=25: (chamadas.append(comando), (0, "", ""))[1]
        degrau = m.DEGRAUS.index("reiniciar-networkmanager")
        nome, rc, _ = m.curar(degrau, None, None)
        self.assertEqual((nome, rc), ("reiniciar-networkmanager", 0))
        self.assertEqual(chamadas,
                         [["sudo", "-n", "systemctl", "restart", "NetworkManager"]])


if __name__ == "__main__":
    unittest.main(verbosity=2)
