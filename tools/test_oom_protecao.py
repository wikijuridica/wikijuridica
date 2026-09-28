#!/usr/bin/env python3
"""test_oom_protecao — o gate de OOM apanha os três defeitos de 2026-09-04?

Gate verde não é prova (R2). Este teste reconstrói, em diretório temporário, os
estados exatos que a auditoria de 2026-09-04 encontrou, e exige que o detector
REPROVE cada um. Sem ele, `check-oom-protecao` poderia estar verde por não
olhar nada.

Descoberto automaticamente por tools/run-qualidade-diaria (glob tools/test_*.py).
"""

import importlib.util
import os
import shutil
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(RAIZ, "tools", "check-oom-protecao")

UNIT_OK = """[Unit]
Description=teste

[Service]
OOMScoreAdjust={valor}
ExecStart=/bin/true
Restart=always
"""

UNIT_SECAO_ERRADA = """[Unit]
Description=teste
OOMScoreAdjust={valor}

[Service]
ExecStart=/bin/true
Restart=always
"""

UNIT_SEM_CHAVE = """[Unit]
Description=teste

[Service]
ExecStart=/bin/true
Restart=always
"""


def carrega_gate():
    spec = importlib.util.spec_from_loader("check_oom_protecao",
                                           SourceFileLoader("check_oom_protecao", GATE))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestSwapDoEarlyoom(unittest.TestCase):
    """O defeito nº 2: `-s 100` deixa o SIGKILL preso atrás do swap."""

    def setUp(self):
        self.gate = carrega_gate()

    def test_s_100_sozinho_e_reprovado(self):
        argv = ["/usr/bin/earlyoom", "-m", "10,5", "-s", "100", "-r", "3600"]
        veredito, detalhe = self.gate.analisa_swap_do_earlyoom(argv)
        self.assertEqual(veredito, "problema", detalhe)
        self.assertIn("50%", detalhe)
        self.assertIn("-s 100,100", detalhe)

    def test_s_100_100_passa(self):
        argv = ["/usr/bin/earlyoom", "-m", "10,5", "-s", "100,100", "-r", "3600"]
        veredito, _ = self.gate.analisa_swap_do_earlyoom(argv)
        self.assertEqual(veredito, "ok")

    def test_forma_colada_s100_tambem_e_apanhada(self):
        """`-s100` é aceito pelo getopt do earlyoom e não pode escapar do gate."""
        veredito, _ = self.gate.analisa_swap_do_earlyoom(["/usr/bin/earlyoom", "-s100"])
        self.assertEqual(veredito, "problema")

    def test_limiares_diferentes_viram_aviso_nao_reprova(self):
        veredito, _ = self.gate.analisa_swap_do_earlyoom(["/usr/bin/earlyoom", "-s", "100,80"])
        self.assertEqual(veredito, "aviso")

    def test_sem_s_e_aviso(self):
        veredito, _ = self.gate.analisa_swap_do_earlyoom(["/usr/bin/earlyoom", "-m", "10,5"])
        self.assertEqual(veredito, "aviso")


class TestSecaoDaChave(unittest.TestCase):
    """O defeito nº 3: OOMScoreAdjust em [Unit] é ignorado em silêncio."""

    def setUp(self):
        self.gate = carrega_gate()

    def test_chave_em_service(self):
        achados = self.gate.secao_da_chave(UNIT_OK.format(valor=-900), "OOMScoreAdjust")
        self.assertEqual(achados, [("[Service]", "-900")])

    def test_chave_em_unit_e_vista_como_unit(self):
        achados = self.gate.secao_da_chave(UNIT_SECAO_ERRADA.format(valor=-900),
                                           "OOMScoreAdjust")
        self.assertEqual(achados, [("[Unit]", "-900")])


class TestRegraUnits(unittest.TestCase):
    """A regra completa, contra árvores ops/systemd fabricadas."""

    def monta(self, conteudos):
        """Cria uma RAIZ falsa com o gate e as units dadas; devolve o módulo."""
        tmp = tempfile.mkdtemp(prefix="oomgate-")
        self.addCleanup(shutil.rmtree, tmp, True)
        os.makedirs(os.path.join(tmp, "tools"))
        os.makedirs(os.path.join(tmp, "ops", "systemd"))
        destino = os.path.join(tmp, "tools", "check-oom-protecao")
        shutil.copy(GATE, destino)
        for nome, texto in conteudos.items():
            with open(os.path.join(tmp, "ops", "systemd", nome), "w",
                      encoding="utf-8") as fh:
                fh.write(texto)
        spec = importlib.util.spec_from_loader(
            "gate_" + os.path.basename(tmp),
            SourceFileLoader("gate_" + os.path.basename(tmp), destino))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def rodar(self, conteudos):
        mod = self.monta(conteudos)
        problemas, avisos = [], []
        mod.regra_units(problemas, avisos)
        return problemas, avisos

    def test_estado_correto_nao_reprova(self):
        problemas, _ = self.rodar({
            "wikijuridica-server.service": UNIT_OK.format(valor=-500),
            "wikijuridica-nginx.service": UNIT_OK.format(valor=-900),
            "cloudflared-wikijuridica.service": UNIT_OK.format(valor=-900),
            "cloudflared-wikijuridica-replica@.service": UNIT_OK.format(valor=-900),
        })
        self.assertEqual(problemas, [])

    def test_chave_na_secao_errada_reprova(self):
        problemas, _ = self.rodar({
            "wikijuridica-server.service": UNIT_SECAO_ERRADA.format(valor=-500),
            "wikijuridica-nginx.service": UNIT_OK.format(valor=-900),
            "cloudflared-wikijuridica.service": UNIT_OK.format(valor=-900),
            "cloudflared-wikijuridica-replica@.service": UNIT_OK.format(valor=-900),
        })
        regras = [p["regra"] for p in problemas]
        self.assertIn("secao", regras, problemas)

    def test_unit_sem_a_chave_reprova(self):
        problemas, _ = self.rodar({
            "wikijuridica-server.service": UNIT_SEM_CHAVE,
            "wikijuridica-nginx.service": UNIT_OK.format(valor=-900),
            "cloudflared-wikijuridica.service": UNIT_OK.format(valor=-900),
            "cloudflared-wikijuridica-replica@.service": UNIT_OK.format(valor=-900),
        })
        self.assertIn("declarado", [p["regra"] for p in problemas])

    def test_valor_fraco_demais_reprova(self):
        """-100 no nginx não cumpre o mínimo de -900."""
        problemas, _ = self.rodar({
            "wikijuridica-server.service": UNIT_OK.format(valor=-500),
            "wikijuridica-nginx.service": UNIT_OK.format(valor=-100),
            "cloudflared-wikijuridica.service": UNIT_OK.format(valor=-900),
            "cloudflared-wikijuridica-replica@.service": UNIT_OK.format(valor=-900),
        })
        self.assertIn("declarado", [p["regra"] for p in problemas])

    def test_menos_1000_reprova_por_pular_a_tarefa(self):
        problemas, _ = self.rodar({
            "wikijuridica-server.service": UNIT_OK.format(valor=-1000),
            "wikijuridica-nginx.service": UNIT_OK.format(valor=-900),
            "cloudflared-wikijuridica.service": UNIT_OK.format(valor=-900),
            "cloudflared-wikijuridica-replica@.service": UNIT_OK.format(valor=-900),
        })
        detalhes = " ".join(p["detalhe"] for p in problemas)
        self.assertIn("LONG_MIN", detalhes)


class TestGateContraORepositorioReal(unittest.TestCase):
    """As units versionadas de verdade cumprem a própria regra."""

    def test_ops_systemd_do_repo_passa_na_regra_units(self):
        mod = carrega_gate()
        problemas, _ = [], []
        problemas, avisos = [], []
        mod.regra_units(problemas, avisos)
        self.assertEqual(problemas, [],
                         "ops/systemd do repositório reprova na própria regra")


class TestSysctlDeclarado(unittest.TestCase):
    """Defeito nº 4: o gate lia só o vivo e ficava verde num host que sobe
    diferente do que roda.

    A fixture usa DIRETÓRIOS DE VERDADE em tempdir, não um dublê da função de
    leitura — senão o teste passaria sem nunca exercitar a precedência do
    sysctl.d(5), que é justamente onde o erro moraria.
    """

    def monta(self, arquivos):
        base = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, base, ignore_errors=True)
        dirs = []
        for sub, conteudos in arquivos:
            d = os.path.join(base, sub)
            os.makedirs(d, exist_ok=True)
            dirs.append(d)
            for nome, texto in conteudos.items():
                with open(os.path.join(d, nome), "w", encoding="utf-8") as fh:
                    fh.write(texto)
        return dirs

    def test_le_o_valor_declarado(self):
        mod = carrega_gate()
        dirs = self.monta([("etc", {"50-a.conf": "vm.overcommit_memory = 1\n"})])
        valor, arquivo = mod.sysctl_declarado("vm.overcommit_memory", dirs)
        self.assertEqual(valor, "1")
        self.assertTrue(arquivo.endswith("50-a.conf"))

    def test_ordena_por_nome_de_arquivo_nao_por_diretorio(self):
        """/usr/lib/99-z vence /etc/10-a: a ordem é o NOME, não o diretório."""
        mod = carrega_gate()
        dirs = self.monta([
            ("etc", {"10-a.conf": "vm.overcommit_memory = 1\n"}),
            ("usrlib", {"99-z.conf": "vm.overcommit_memory = 0\n"}),
        ])
        valor, arquivo = mod.sysctl_declarado("vm.overcommit_memory", dirs)
        self.assertEqual(valor, "0")
        self.assertTrue(arquivo.endswith("99-z.conf"))

    def test_mesmo_nome_o_primeiro_diretorio_vence(self):
        """/etc mascara /usr/lib quando o nome do arquivo se repete."""
        mod = carrega_gate()
        dirs = self.monta([
            ("etc", {"50-x.conf": "vm.overcommit_memory = 0\n"}),
            ("usrlib", {"50-x.conf": "vm.overcommit_memory = 1\n"}),
        ])
        valor, _ = mod.sysctl_declarado("vm.overcommit_memory", dirs)
        self.assertEqual(valor, "0")

    def test_ignora_comentario_e_chave_parecida(self):
        mod = carrega_gate()
        dirs = self.monta([("etc", {"50-a.conf":
                                    "# vm.overcommit_memory = 1\n"
                                    "vm.overcommit_memory_foo = 1\n"
                                    "vm.overcommit_ratio = 100\n"})])
        valor, _ = mod.sysctl_declarado("vm.overcommit_memory", dirs)
        self.assertIsNone(valor)

    def test_aceita_prefixo_de_erro_tolerado(self):
        """sysctl.d(5): '-chave' significa 'não falhe se não existir'."""
        mod = carrega_gate()
        dirs = self.monta([("etc", {"50-a.conf": "-vm.overcommit_memory = 1\n"})])
        valor, _ = mod.sysctl_declarado("vm.overcommit_memory", dirs)
        self.assertEqual(valor, "1")

    def test_divergencia_declarado_x_vivo_REPROVA(self):
        """O coração do defeito nº 4: vivo=0 e declarado=1 tem de reprovar.

        Sem este teste o gate ficaria verde num host que roda heurístico hoje
        e sobe em 'always overcommit' no próximo boot.
        """
        mod = carrega_gate()
        dirs = self.monta([("etc", {"50-a.conf": "vm.overcommit_memory = 1\n"})])
        problemas, avisos = [], []
        orig = mod.DIRS_SYSCTL
        mod.DIRS_SYSCTL = tuple(dirs)
        # sysctl_declarado usa DIRS_SYSCTL como default do parâmetro, que foi
        # ligado na definição — então a regra é chamada com o valor explícito
        # através de um patch do próprio wrapper, para exercitar o caminho real.
        real = mod.sysctl_declarado
        mod.sysctl_declarado = lambda chave, d=tuple(dirs): real(chave, d)
        try:
            mod.regra_overcommit(problemas, avisos)
        finally:
            mod.sysctl_declarado = real
            mod.DIRS_SYSCTL = orig
        vivo = mod.ler_int("/proc/sys/vm/overcommit_memory")
        if vivo == 1:
            self.skipTest("host vivo já está em 1; a divergência não existe aqui")
        detalhes = " ".join(p["detalhe"] for p in problemas)
        self.assertTrue(problemas, "divergência declarado x vivo passou batido")
        self.assertIn("declara 1", detalhes)
        self.assertIn("próximo reboot", detalhes)

    def test_host_real_declarado_bate_com_vivo(self):
        """No host de verdade os dois lados têm de concordar."""
        mod = carrega_gate()
        declarado, arquivo = mod.sysctl_declarado("vm.overcommit_memory")
        if declarado is None:
            self.skipTest("nenhum sysctl.d declara vm.overcommit_memory")
        vivo = mod.ler_int("/proc/sys/vm/overcommit_memory")
        if vivo is None:
            self.skipTest("sem /proc/sys/vm/overcommit_memory")
        self.assertEqual(int(declarado), vivo,
                         f"{arquivo} declara {declarado} e o host roda {vivo}: "
                         "a máquina sobe diferente do que está rodando")


if __name__ == "__main__":
    unittest.main(verbosity=2)
