#!/usr/bin/env python3
"""Prova o TERCEIRO ESTADO (exit 2 = NAO MEDI) nas quatro sondas que so sabiam 0 e 1.

Ate 2026-09-16, `check-tunnel-health`, `check-fontes-alcancaveis`,
`check-network-health` e `check-portal-health` nao tinham caminho de saida >= 2
NENHUM. Como as units delas mascaram exit 1 (`SuccessExitStatus=0 1`), a falta
de medicao saia como veredito e virava `Result=success`: para essas quatro, a
mascara apagava o UNICO sinal que existia.

────────────────────────────────────────────────────────────────────────────
AS DUAS METADES, E A DE BAIXO E A QUE EVITA ALARME FALSO

Cada sonda e exercitada em DOIS mundos:

  (1) a dependencia responde  -> rc in {0, 1}. Um 2 aqui seria alarme ao dono a
      cada ciclo do timer, porque as quatro units declaram OnFailure. Medido em
      2026-09-16 contra a producao viva: frota=5 instancias, registry=58 fontes,
      `ip -V` rc=0, NRestarts legivel — nenhuma das quatro guardas dispara hoje.
  (2) a dependencia NAO responde -> rc == 2 e a frase-ancora `NAO MEDIDO:` no
      stderr.

────────────────────────────────────────────────────────────────────────────
POR QUE NENHUM `main()` COMPLETO E CHAMADO AQUI

As quatro sondam a rede, reiniciam unit com `--repair` e gravam estado — e
`check-portal-health` grava `data/ops/portal_health_state.json`, que e
RASTREADO. Um teste que rodasse o main inteiro mediria a producao e sujaria o
disco a cada execucao da bancada.

O que se exercita e a GUARDA, no ponto em que ela decide — e as guardas foram
movidas, de proposito, para ANTES de reparar/alertar/gravar. Essa posicao e
parte da correcao: agir sobre medicao cega e pior que nao agir, e este vigia ja
piorou uma vez o estado que tentava consertar (2026-08-15, quatro reinicios em
3m20s).
"""

import importlib.machinery
import importlib.util
import io
import os
import sys
import unittest
from contextlib import redirect_stderr

RAIZ = os.environ.get("WIKI_ROOT", "/opt/wiki")


def carrega(nome, ferramenta):
    """Carrega ferramenta SEM extensao .py, pelo caminho explicito.

    Mesmo idioma de tools/check-social-cache:37, e pelo mesmo motivo: evita o
    `sys.path.insert` + import que obrigaria a um `# noqa: E402`, e suprimir o
    diagnostico em vez de resolver a causa e proibido neste repositorio.
    """
    caminho = os.path.join(RAIZ, "tools", ferramenta)
    carregador = importlib.machinery.SourceFileLoader(nome, caminho)
    spec = importlib.util.spec_from_loader(nome, carregador)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


class TerceiroEstado(unittest.TestCase):
    maxDiff = None

    # ────────────────────────────────────────────────────────────────────
    # check-fontes-alcancaveis — registry vazio sondava ZERO hosts e imprimia
    # "pass". Zero fonte sondada nao e "todas as fontes vivas".
    def test_fontes_registry_vazio_nao_e_pass(self):
        m = carrega("fa_vazio", "check-fontes-alcancaveis")
        m.coleta_enderecos = lambda *a, **k: []
        erro = io.StringIO()
        argv = sys.argv
        sys.argv = ["check-fontes-alcancaveis"]
        try:
            with redirect_stderr(erro):
                rc = m.main()
        finally:
            sys.argv = argv
        self.assertEqual(rc, 2, "registry vazio TEM de sair 2, nunca 0 ('pass')")
        self.assertIn("NAO MEDIDO:", erro.getvalue())

    def test_fontes_registry_vivo_nao_dispara_a_guarda(self):
        """Controle negativo sobre o disco real: 58 fontes hoje."""
        m = carrega("fa_vivo", "check-fontes-alcancaveis")
        self.assertGreater(
            len(m.coleta_enderecos()), 0,
            "o registry real esta vazio: a guarda dispararia em producao a cada ciclo")

    # ────────────────────────────────────────────────────────────────────
    # check-tunnel-health — frota vazia pulava a guarda inteira
    # (`if frota_total and ...`) e saia 0 tendo sondado zero replicas.
    def test_tunnel_frota_invisivel_nao_e_ok(self):
        m = carrega("th_vazio", "check-tunnel-health")
        m.sondar_frota = lambda *a, **k: (0, [], 0, [])
        m.ler_json = lambda *a, **k: ({"readyConnections": 4}, None)
        m.ler_metricas = lambda *a, **k: ("", None)
        m.metrica = lambda *a, **k: 0
        m.rota_v6_caindo = lambda *a, **k: 0
        m.link_caido = lambda *a, **k: (False, "")
        m.carregar_estado = lambda *a, **k: {}
        # Sentinelas: se a guarda NAO sair antes destes, o teste falha alto em
        # vez de gravar estado ou alertar o dono de verdade.
        def proibido(*a, **k):
            raise AssertionError("a guarda tinha de sair ANTES de gravar/alertar")
        m.gravar_estado = proibido
        m.anexar_historico = proibido
        m.avisar_dono = proibido
        erro = io.StringIO()
        argv = sys.argv
        sys.argv = ["check-tunnel-health"]
        try:
            with redirect_stderr(erro):
                rc = m.main()
        finally:
            sys.argv = argv
        self.assertEqual(rc, 2, "frota invisivel TEM de sair 2, nunca 0")
        self.assertIn("NAO MEDIDO:", erro.getvalue())

    def test_tunnel_frota_real_nao_dispara_a_guarda(self):
        """Controle negativo: 5 instancias hoje (CLAUDE.md §3 diz 5, nao 25)."""
        m = carrega("th_vivo", "check-tunnel-health")
        self.assertGreater(
            len(m.descobrir_frota()), 0,
            "a frota real esta vazia: a guarda alertaria o dono a cada 2 min")

    # ────────────────────────────────────────────────────────────────────
    # check-network-health — (None, None) de descobrir_interface confundia
    # "nao ha rota default" (VEREDITO) com "nao ha o utilitario ip" (DEFEITO).
    def test_network_sem_o_utilitario_ip_e_defeito_nao_veredito(self):
        m = carrega("nh_sem_ip", "check-network-health")
        m.rodar = lambda *a, **k: (127, "", "[Errno 2] No such file or directory: 'ip'")
        def proibido(*a, **k):
            raise AssertionError("a guarda tinha de sair ANTES de curar/gravar")
        m.curar = proibido
        m.gravar_estado = getattr(m, "gravar_estado", proibido)
        erro = io.StringIO()
        argv = sys.argv
        sys.argv = ["check-network-health"]
        try:
            with redirect_stderr(erro):
                rc = m.main()
        finally:
            sys.argv = argv
        self.assertEqual(rc, 2, "sem o utilitario `ip` o resultado e 2 (nao medi), nao 1")
        self.assertIn("NAO MEDIDO:", erro.getvalue())

    def test_network_com_ip_presente_nao_dispara_a_guarda(self):
        m = carrega("nh_vivo", "check-network-health")
        rc, _, _ = m.rodar(["ip", "-V"], timeout=5)
        self.assertNotEqual(rc, 127, "`ip` ausente neste host: a guarda dispararia sempre")

    # ────────────────────────────────────────────────────────────────────
    # check-portal-health — `except Exception: return ""` fazia NRestarts virar
    # 0, o delta virar 0 e o detector de laco de restart ficar cego dizendo OK.
    def test_portal_systemd_ilegivel_deixa_rastro_e_sai_2(self):
        m = carrega("ph_cego", "check-portal-health")
        m.FALHAS_SYSTEMD.clear()

        def systemctl_quebrado(*a, **k):
            raise OSError("systemctl nao encontrado")

        # `m.subprocess` E O MODULO STDLIB COMPARTILHADO, nao uma copia por
        # ferramenta: sem o `finally` abaixo, este patch vaza para todos os
        # testes seguintes do processo. Custou uma execucao vermelha desta
        # bancada em 2026-09-16 — o teste do controle NEGATIVO acusou o rastro
        # que ESTE teste tinha deixado, e a leitura apressada seria culpar a
        # ferramenta.
        original = m.subprocess.run
        try:
            m.subprocess.run = systemctl_quebrado
            # O proprio helper tem de CAPTURAR e REGISTRAR: e o `return ""` mudo
            # que era o defeito, nao a excecao.
            valor = m.systemd_propriedade("NRestarts")
        finally:
            m.subprocess.run = original
        self.assertEqual(valor, "")
        self.assertTrue(
            m.FALHAS_SYSTEMD,
            "a falha de leitura do systemd TEM de deixar rastro; era o `except "
            "Exception: return ''` mudo que cegava o detector de laco de restart")
        m.FALHAS_SYSTEMD.clear()

    def test_portal_systemd_legivel_nao_dispara_a_guarda(self):
        m = carrega("ph_vivo", "check-portal-health")
        m.FALHAS_SYSTEMD.clear()
        m.systemd_propriedade("NRestarts")
        self.assertEqual(
            m.FALHAS_SYSTEMD, [],
            "systemctl ilegivel neste host: o watchdog sairia 2 a cada 2 min")


if __name__ == "__main__":
    unittest.main(verbosity=2)
