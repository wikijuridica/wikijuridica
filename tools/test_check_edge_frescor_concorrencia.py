"""Bancada da guarda de concorrência de tools/check-edge-frescor.

POR QUE ELA EXISTE. Em 2026-09-10 rodei a sonda de borda e o aquecedor de borda
ao mesmo tempo. As duas medem o MESMO canal, e a que chega em segundo mede a
degradação que a primeira causou:

    warm-edge-cache --rps 12 --so-frios, com a sonda junto
        11210 em 1015s (11,05 r/s)   status {200: 10430, 0: 780}
    a mesma passada, sozinha
        11210 em  934s (12,00 r/s)   status {200: 11210}

    check-edge-frescor, na janela concorrente:  521 erros_de_sonda
    check-edge-frescor, depois:                   0 erros_de_sonda

Nenhum desses números ruins era sobre o portal — as páginas serviam 200 com
`cf-cache-status: HIT` o tempo todo. O aquecedor já tinha trava própria contra
outro aquecedor (`warm-edge-cache:58`); o que faltava era a sonda consultá-la.

NUNCA `pkill -f`: o padrão casa a própria linha de comando do teste e já matou o
shell de quem o rodou neste repositório. O processo auxiliar nasce em sessão
própria e morre por `os.killpg`.
"""
import fcntl
import os
import re
import signal
import subprocess
import sys
import tempfile
import textwrap
import types
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
GATE = RAIZ / "tools/check-edge-frescor"


def carrega():
    """Recorta a função REAL do gate — nunca uma cópia, que continuaria passando
    depois de alguém mudar o original. Carrega por compile() do texto, não por
    SourceFileLoader: bytecode obsoleto já cegou prova por mutação nesta casa."""
    fonte = GATE.read_text(encoding="utf-8")
    inicio = fonte.index('LOCK_AQUECIMENTO = "')
    fim = fonte.index("def main(", inicio)
    modulo = types.ModuleType("check_edge_frescor_concorrencia")
    exec(compile("import fcntl, os\n" + fonte[inicio:fim], str(GATE), "exec"), modulo.__dict__)
    return modulo


MODULO = carrega()


class TravaCompartilhada(unittest.TestCase):
    def setUp(self):
        descritor, self.caminho = tempfile.mkstemp(prefix="warm-edge-cache-teste-")
        os.close(descritor)
        self.filhos = []

    def tearDown(self):
        for processo in self.filhos:
            try:
                os.killpg(os.getpgid(processo.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            processo.wait(timeout=10)
        os.unlink(self.caminho)

    def segura_exclusivo(self):
        """Um processo separado toma LOCK_EX e fica vivo — é o aquecedor."""
        script = textwrap.dedent("""
            import fcntl, sys, time
            arquivo = open(sys.argv[1], "a+")
            fcntl.flock(arquivo.fileno(), fcntl.LOCK_EX)
            sys.stdout.write("preso\\n"); sys.stdout.flush()
            time.sleep(120)
        """)
        processo = subprocess.Popen([sys.executable, "-c", script, self.caminho],
                                    stdout=subprocess.PIPE, text=True, start_new_session=True)
        self.filhos.append(processo)
        self.assertEqual(processo.stdout.readline().strip(), "preso")
        return processo

    def test_sem_aquecimento_a_sonda_pode_medir(self):
        self.assertFalse(MODULO.aquecimento_em_voo(self.caminho))

    def test_com_aquecimento_em_voo_a_sonda_detecta(self):
        self.segura_exclusivo()
        self.assertTrue(MODULO.aquecimento_em_voo(self.caminho))

    def test_a_trava_volta_a_liberar_quando_o_aquecimento_sai(self):
        processo = self.segura_exclusivo()
        self.assertTrue(MODULO.aquecimento_em_voo(self.caminho))
        os.killpg(os.getpgid(processo.pid), signal.SIGKILL)
        processo.wait(timeout=10)
        self.assertFalse(MODULO.aquecimento_em_voo(self.caminho))

    def test_lock_inexistente_nao_bloqueia(self):
        """Máquina que nunca rodou o aquecedor não tem o arquivo — e isso não é
        motivo para recusar medição."""
        self.assertFalse(MODULO.aquecimento_em_voo(self.caminho + ".nao-existe"))

    def test_duas_sondas_nao_se_atrapalham(self):
        """A trava é tomada em modo COMPARTILHADO: o que precisa ser detectado é
        o aquecedor, que a toma em exclusivo. Duas sondas não escrevem nada."""
        outra = open(self.caminho, "a+")
        fcntl.flock(outra.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
        try:
            self.assertFalse(MODULO.aquecimento_em_voo(self.caminho))
        finally:
            outra.close()


class LigacaoNoGate(unittest.TestCase):
    """A função existir não basta: o `main` tem de consultá-la e sair com 2."""

    def test_o_main_consulta_a_guarda(self):
        fonte = GATE.read_text(encoding="utf-8")
        self.assertIn("if deps is None and aquecimento_em_voo():", fonte)

    def test_o_veredito_e_inconclusivo_e_nao_vermelho(self):
        """2, nunca 1. Medir durante aquecimento não é 'a borda está velha': é
        'não dá para saber'. Vermelho mandaria purgar rota fresca."""
        fonte = GATE.read_text(encoding="utf-8")
        trecho = fonte[fonte.index("if deps is None and aquecimento_em_voo():"):]
        trecho = trecho[:trecho.index("deps = deps or dependencias_reais()")]
        self.assertIn("return 2", trecho)
        self.assertNotIn("return 1", trecho)

    def test_a_guarda_usa_a_trava_do_aquecedor_e_nao_uma_propria(self):
        """Dois caminhos de trava seriam duas listas da mesma coisa — o defeito
        que este repositório catalogou três vezes em 2026-09-10."""
        do_gate = re.search(r'LOCK_AQUECIMENTO = "([^"]+)"', GATE.read_text(encoding="utf-8"))
        do_aquecedor = re.search(r'LOCK_AQUECIMENTO = "([^"]+)"',
                                 (RAIZ / "tools/warm-edge-cache").read_text(encoding="utf-8"))
        self.assertIsNotNone(do_gate)
        self.assertIsNotNone(do_aquecedor)
        self.assertEqual(do_gate.group(1), do_aquecedor.group(1))


if __name__ == "__main__":
    unittest.main()
