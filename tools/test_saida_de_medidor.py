#!/usr/bin/env python3
"""Prova que tools/lib/saida_de_medidor.py converte QUEDA em exit 2 — e so queda.

A prova que importa e o PAR: a MESMA ferramenta, que levanta a MESMA excecao,
sai com 1 sob o rodape antigo (`sys.exit(main())`) e com 2 sob o novo
(`main_protegido(main)`). Um teste que so exercitasse o rodape novo mostraria um
2 sem provar que ele veio da correcao — e o precedente
`teste-que-reimplementa-nao-testa` deste repositorio.

E a metade de baixo importa tanto quanto: veredito 1 legitimo, exit 0 e o
`SystemExit(2)` do argparse TEM de passar intactos. Um helper que promovesse
todo 1 a 2 transformaria o veredito de rotina de 19 units em enxurrada de
alarme, que e como se treina um dono a ignorar o canal.
"""

import os
import subprocess
import sys
import tempfile
import textwrap
import unittest

RAIZ = os.environ.get("WIKI_ROOT", "/opt/wiki")
LIB = os.path.join(RAIZ, "tools", "lib")

# O rodape ANTIGO e o NOVO, lado a lado. A unica diferenca entre as duas
# ferramentas geradas abaixo e qual destes dois blocos entra no fim do arquivo.
RODAPE_ANTIGO = "sys.exit(main())"
RODAPE_NOVO = textwrap.dedent(
    """
    sys.path.insert(0, LIB_DIR)
    from saida_de_medidor import main_protegido
    main_protegido(main)
    """
).strip()


def ferramenta(corpo_do_main, rodape):
    """Escreve uma ferramenta de verdade em disco e devolve o caminho."""
    fonte = textwrap.dedent(
        """
        import sys
        LIB_DIR = {lib!r}

        def main():
        {corpo}

        if __name__ == "__main__":
        {rodape}
        """
    ).format(
        lib=LIB,
        corpo=textwrap.indent(textwrap.dedent(corpo_do_main).strip(), "    "),
        rodape=textwrap.indent(rodape, "    "),
    )
    fh = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8")
    fh.write(fonte)
    fh.close()
    return fh.name


def roda(caminho, *args):
    proc = subprocess.run(
        [sys.executable, caminho, *args], capture_output=True, text=True, timeout=60
    )
    return proc.returncode, proc.stdout + proc.stderr


class QuedaViraDois(unittest.TestCase):
    # A ferramenta cai no meio da medicao, do jeito mais comum: uma chave que
    # sumiu do JSON que ela le.
    CORPO_QUE_CAI = """
        dados = {"conexoes": 4}
        print("sondando...")
        return 1 if dados["ha"] < 4 else 0
    """

    def test_par_antes_e_depois(self):
        """O PAR: mesma queda, 1 com o rodape antigo, 2 com o novo."""
        antiga = ferramenta(self.CORPO_QUE_CAI, RODAPE_ANTIGO)
        nova = ferramenta(self.CORPO_QUE_CAI, RODAPE_NOVO)
        try:
            rc_antes, saida_antes = roda(antiga)
            rc_depois, saida_depois = roda(nova)
        finally:
            os.unlink(antiga)
            os.unlink(nova)

        self.assertEqual(
            rc_antes, 1,
            "ANTES: a queda tinha de colapsar em 1 (e o defeito que o helper corrige). "
            "Saida: %s" % saida_antes[-400:],
        )
        self.assertEqual(
            rc_depois, 2,
            "DEPOIS: a queda tem de sair 2. Se isto virar 1, a correcao foi desfeita "
            "e a unit voltou a mascarar crash como veredito. Saida: %s" % saida_depois[-400:],
        )
        # O diagnostico nao pode se perder na traducao do codigo.
        self.assertIn("KeyError", saida_depois, "o traceback tem de sobreviver inteiro")
        self.assertIn("NAO MEDIDO:", saida_depois, "a frase-ancora tem de sair no stderr")
        # E a frase NAO pode aparecer no caminho antigo: se aparecesse nos dois,
        # o teste nao estaria medindo a diferenca.
        self.assertNotIn("NAO MEDIDO:", saida_antes)


class VereditoLegitimoPassaIntacto(unittest.TestCase):
    """A metade que impede o falso positivo em massa."""

    def test_return_1_continua_1(self):
        alvo = ferramenta('print("medi"); return 1', RODAPE_NOVO)
        try:
            rc, saida = roda(alvo)
        finally:
            os.unlink(alvo)
        self.assertEqual(rc, 1, "veredito medido 'degradado' TEM de continuar 1")
        self.assertNotIn("NAO MEDIDO:", saida)

    def test_return_0_continua_0(self):
        alvo = ferramenta('print("medi"); return 0', RODAPE_NOVO)
        try:
            rc, _ = roda(alvo)
        finally:
            os.unlink(alvo)
        self.assertEqual(rc, 0)

    def test_return_2_deliberado_continua_2(self):
        alvo = ferramenta('print("inconclusivo"); return 2', RODAPE_NOVO)
        try:
            rc, _ = roda(alvo)
        finally:
            os.unlink(alvo)
        self.assertEqual(rc, 2, "o `return 2` que a ferramenta ja tinha nao pode mudar")

    def test_systemexit_deliberado_propaga(self):
        alvo = ferramenta('sys.exit(3)', RODAPE_NOVO)
        try:
            rc, _ = roda(alvo)
        finally:
            os.unlink(alvo)
        self.assertEqual(rc, 3, "SystemExit deliberado dentro do main propaga sem reescrita")

    def test_argparse_invocacao_invalida_continua_2(self):
        corpo = """
            import argparse
            ap = argparse.ArgumentParser()
            ap.add_argument("--horas", type=int)
            ap.parse_args()
            return 0
        """
        alvo = ferramenta(corpo, RODAPE_NOVO)
        try:
            rc, saida = roda(alvo, "--flag-que-nao-existe")
        finally:
            os.unlink(alvo)
        # argparse levanta SystemExit(2); o helper propaga. O codigo ja e o certo
        # (invocacao invalida E defeito de processo), e nao ha traceback a imprimir.
        self.assertEqual(rc, 2)
        self.assertNotIn("Traceback", saida)


class FerramentasDasUnitsEstaoProtegidas(unittest.TestCase):
    """Guarda de regressao sobre o disco real, nao sobre fixture.

    Sem isto, uma ferramenta nova chamada por unit que mascara exit 1 nasceria
    sem protecao e nada reprovaria. A lista sai das units, nao de nomes soltos.
    """

    def test_rodape_protegido_nas_ferramentas_convertidas(self):
        esperadas = [
            "check-tunnel-health", "check-fontes-alcancaveis", "check-network-health",
            "check-portal-health", "check-edge-live", "check-crawler-error-budget",
            "check-efeito-nos-bots", "check-edge-cache-coverage", "check-edge-frescor",
            "check-owner-alerts-abertos", "generate-alertas-reconciliados",
            "warm-edge-cache", "check-units-alarme",
        ]
        faltando = []
        for nome in esperadas:
            caminho = os.path.join(RAIZ, "tools", nome)
            if not os.path.exists(caminho):
                faltando.append("%s (arquivo ausente)" % nome)
                continue
            with open(caminho, encoding="utf-8", errors="replace") as fh:
                fonte = fh.read()
            if "main_protegido" not in fonte:
                faltando.append("%s (sem main_protegido)" % nome)
        self.assertEqual(
            faltando, [],
            "ferramenta chamada por unit que mascara exit 1 sem a protecao crash->2: %s"
            % faltando,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
