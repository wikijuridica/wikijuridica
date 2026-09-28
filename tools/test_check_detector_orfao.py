#!/usr/bin/env python3
"""Bancada de tools/check-detector-orfao — o gate que mata a familia do detector orfao.

FIXTURE PROPRIA, NUNCA O DISCO VIVO. O precedente que obriga isto e' desta
sessao: um mutante sobreviveu porque o shard de acordaos PASSOU A EXISTIR no
meio do dia e a fixture emprestada do disco parou de exercitar o cenario. Aqui
cada caso monta uma arvore com `git init` proprio, tres a cinco arquivos, e
passa `--piso-populacao/--piso-raizes` correspondentes — travar a fixture no
piso de producao mediria o tamanho da fixture, nao o predicado.

CONTROLE PAREADO EM TODO CASO: o mesmo cenario SEM o defeito sai 0. Sem ele o
teste passa por qualquer outro problema da fixture, o que ja aconteceu nesta
sessao.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(RAIZ, "tools", "check-detector-orfao")

VIGIA_COM_GLOBS = """#!/usr/bin/env bash
# vigia de fixture
for teste in "$RAIZ"/tools/test_*.py; do
\t[ -f "$teste" ] || continue
done
for teste in "$RAIZ"/tools/*-selftest; do
\t[ -f "$teste" ] || continue
done
"""


def escreve(caminho, texto, executavel=False):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(texto)
    if executavel:
        os.chmod(caminho, 0o755)


class Arvore:
    """Arvore de fixture com git proprio — o gate le `git ls-files`."""

    def __init__(self):
        self.raiz = tempfile.mkdtemp(prefix="detector-orfao-")
        subprocess.run(["git", "init", "-q"], cwd=self.raiz, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        escreve(os.path.join(self.raiz, "tools/run-qualidade-diaria"), VIGIA_COM_GLOBS, True)
        # RAIZ MINIMA. O piso de raizes e' controle positivo do gate: com zero
        # raiz "todo detector parece orfao", e o veredito passa a ser sobre o
        # instrumento (exit 2) em vez de sobre o codigo. A fixture nasce com UMA
        # raiz que nao liga nada — um teste vazio que casa o glob do vigia — para
        # que cada caso meca o predicado, e nao a ausencia de raizes.
        escreve(os.path.join(self.raiz, "tools/test_fixture.py"),
                "# raiz de fixture: casa o glob do vigia e nao chama ninguem\n")

    def detector(self, nome, corpo="#!/usr/bin/env python3\nprint('ok')\n"):
        escreve(os.path.join(self.raiz, "tools", nome), corpo, True)

    def arquivo(self, rel, corpo):
        escreve(os.path.join(self.raiz, rel), corpo)

    def registro(self, linhas):
        corpo = "# registro de fixture\n" + "".join(
            json.dumps(l, ensure_ascii=False, sort_keys=True) + "\n" for l in linhas)
        escreve(os.path.join(self.raiz, "ops/detectores-decididos.jsonl"), corpo)

    def roda(self, piso_pop=1, piso_raizes=1):
        proc = subprocess.run(
            [sys.executable, GATE, "--raiz", self.raiz,
             "--piso-populacao", str(piso_pop), "--piso-raizes", str(piso_raizes)],
            capture_output=True, text=True)
        return proc.returncode, proc.stdout + proc.stderr

    def censo(self):
        proc = subprocess.run([sys.executable, GATE, "--raiz", self.raiz, "--json"],
                              capture_output=True, text=True, check=True)
        return json.loads(proc.stdout)

    def fim(self):
        shutil.rmtree(self.raiz, ignore_errors=True)


class TestDetectorOrfao(unittest.TestCase):
    def setUp(self):
        self.a = Arvore()
        self.addCleanup(self.a.fim)

    # ------------------------------------------------------------------ nucleo
    def test_orfao_sem_registro_reprova_e_o_controle_ligado_sai_zero(self):
        """O par que define o gate: orfao reprova; o MESMO detector, ligado, sai 0."""
        self.a.detector("check-coisa")
        rc, saida = self.a.roda()
        self.assertEqual(rc, 1, f"orfao sem registro tinha de reprovar; saida:\n{saida}")
        self.assertIn("check-coisa", saida)
        self.assertIn("DETECTOR ORFAO NOVO", saida)

        # CONTROLE: a unica mudanca e' uma unit que o executa.
        self.a.arquivo("ops/systemd/fixture.service",
                       "[Service]\nExecStart=/opt/x/tools/check-coisa\n")
        rc2, saida2 = self.a.roda()
        self.assertEqual(rc2, 0, f"com executor o gate tinha de sair 0; saida:\n{saida2}")

    def test_mencao_em_comentario_nao_liga_ninguem(self):
        """A armadilha medida em run-daily-content:446-447.

        Comentario citando o comando dava a impressao de que ele rodava. Se o
        gate contasse comentario, este caso sairia 0 — e o orfao seguiria
        invisivel.
        """
        self.a.detector("check-coisa")
        # O RUNNER QUE MENCIONA PRECISA ESTAR ENRAIZADO, senao a fixture nao
        # exercita o caso: a primeira versao deste teste deixava `run-outro`
        # fora de qualquer raiz, e o mutante que faz COMENTARIO VIRAR ARESTA
        # SOBREVIVEU — o alvo continuava orfao por falta de raiz, nao por causa
        # do comentario. Com a unit aqui, a UNICA diferenca entre reprovar e
        # passar e' o caractere `#`.
        self.a.arquivo("ops/systemd/fixture.service",
                       "[Service]\nExecStart=/opt/x/tools/run-outro\n")
        self.a.arquivo("tools/run-outro",
                       "#!/usr/bin/env bash\n# aqui rodaria tools/check-coisa, mas nao roda\necho nada\n")
        rc, saida = self.a.roda()
        self.assertEqual(rc, 1, f"mencao em comentario NAO e executor; saida:\n{saida}")
        self.assertIn("check-coisa", saida)

        # CONTROLE PAREADO: a MESMA arvore, a MESMA linha, sem o `#`.
        self.a.arquivo("tools/run-outro",
                       '#!/usr/bin/env bash\n"$RAIZ/tools/check-coisa"\n')
        rc2, saida2 = self.a.roda()
        self.assertEqual(rc2, 0, f"invocacao real tinha de ligar; saida:\n{saida2}")

    def test_chamado_por_quem_tambem_nao_roda_continua_orfao(self):
        """Alcancabilidade, nao mencao: a cadeia tem de comecar numa raiz."""
        self.a.detector("check-coisa")
        self.a.detector("generate-intermediario",
                        '#!/usr/bin/env bash\n"$RAIZ/tools/check-coisa"\n')
        rc, saida = self.a.roda()
        self.assertEqual(rc, 1, f"cadeia de orfaos nao liga ninguem; saida:\n{saida}")
        self.assertIn("check-coisa", saida)
        self.assertIn("generate-intermediario", saida)

        # CONTROLE: basta enraizar o intermediario para os DOIS ficarem ligados.
        self.a.arquivo("ops/systemd/fixture.service",
                       "[Service]\nExecStart=/opt/x/tools/generate-intermediario\n")
        rc2, saida2 = self.a.roda()
        self.assertEqual(rc2, 0, f"raiz -> intermediario -> alvo tinha de ligar os dois; saida:\n{saida2}")

    def test_teste_que_so_nomeia_nao_e_executor(self):
        """internal/redesocialcompletude/integracao_test.go:71 faz os.Stat e nada mais.

        Contar isso como executor e' o falso-verde que este gate existe para
        matar: o detector aparece coberto e ninguem nunca roda o predicado.
        """
        self.a.detector("check-coisa")
        self.a.arquivo("internal/x/x_test.go",
                       'package x\nimport "os"\nfunc TestQ(t *T) { os.Stat("tools/check-coisa") }\n')
        rc, saida = self.a.roda()
        self.assertEqual(rc, 1, f"teste que so nomeia nao executa o predicado; saida:\n{saida}")

        # CONTROLE: o mesmo teste, agora EXECUTANDO.
        self.a.arquivo("internal/x/x_test.go",
                       'package x\nimport "os/exec"\nfunc TestQ(t *T) { exec.Command("tools/check-coisa").Run() }\n')
        rc2, saida2 = self.a.roda()
        self.assertEqual(rc2, 0, f"exec.Command tinha de ligar; saida:\n{saida2}")

    def test_glob_do_vigia_e_lido_do_vigia(self):
        """Se o vigia perde o glob, as raizes somem — e o gate acusa o INSTRUMENTO."""
        self.a.detector("check-coisa-selftest")
        rc, saida = self.a.roda()
        self.assertEqual(rc, 0, f"selftest e' raiz pelo glob do vigia; saida:\n{saida}")

        escreve(os.path.join(self.a.raiz, "tools/run-qualidade-diaria"),
                "#!/usr/bin/env bash\necho sem glob nenhum\n", True)
        rc2, saida2 = self.a.roda()
        self.assertEqual(rc2, 2, f"vigia sem glob e' defeito de INSTRUMENTO (exit 2); saida:\n{saida2}")
        self.assertIn("INSTRUMENTO", saida2)

    def test_piso_de_deteccao_e_controle_positivo(self):
        """Varredura que nao enxerga nada tem de acusar o detector, nao o codigo."""
        self.a.detector("check-coisa")
        self.a.arquivo("ops/systemd/fixture.service",
                       "[Service]\nExecStart=/opt/x/tools/check-coisa\n")
        rc, saida = self.a.roda(piso_pop=1, piso_raizes=1)
        self.assertEqual(rc, 0, f"controle: com piso compativel sai 0; saida:\n{saida}")

        rc2, saida2 = self.a.roda(piso_pop=500, piso_raizes=1)
        self.assertEqual(rc2, 2, f"populacao abaixo do piso e' veredito sobre o INSTRUMENTO; saida:\n{saida2}")
        self.assertIn("varredura cega", saida2)

    # ------------------------------------------------- as duas direcoes do registro
    def test_registro_absolve_orfao_decidido(self):
        self.a.detector("check-coisa")
        self.a.registro([{"ferramenta": "tools/check-coisa", "classe": "datado",
                          "destino": "arquivar-migracao-datada", "motivo": "migracao de uma vez",
                          "decidido_em": "2026-09-16"}])
        rc, saida = self.a.roda()
        self.assertEqual(rc, 0, f"orfao com decisao escrita nao e entrada nova; saida:\n{saida}")

    def test_registro_com_campo_vazio_reprova(self):
        """Decisao sem motivo nao e' decisao: e' allowlist disfarcada."""
        self.a.detector("check-coisa")
        self.a.registro([{"ferramenta": "tools/check-coisa", "classe": "datado",
                          "destino": "arquivar-migracao-datada", "motivo": "",
                          "decidido_em": "2026-09-16"}])
        rc, saida = self.a.roda()
        self.assertEqual(rc, 1, f"campo obrigatorio vazio tinha de reprovar; saida:\n{saida}")
        self.assertIn("motivo", saida)

    def test_linha_para_ferramenta_que_sumiu_reprova(self):
        self.a.detector("check-coisa")
        self.a.registro([
            {"ferramenta": "tools/check-coisa", "classe": "datado", "destino": "arquivar-migracao-datada",
             "motivo": "migracao", "decidido_em": "2026-09-16"},
            {"ferramenta": "tools/check-que-nao-existe", "classe": "datado",
             "destino": "arquivar-migracao-datada", "motivo": "migracao", "decidido_em": "2026-09-16"}])
        rc, saida = self.a.roda()
        self.assertEqual(rc, 1, f"linha para ferramenta morta esconde o backlog real; saida:\n{saida}")
        self.assertIn("check-que-nao-existe", saida)

    def test_linha_para_ferramenta_que_ja_tem_executor_reprova(self):
        """Registro que descreve o passado mente sobre o presente."""
        self.a.detector("check-coisa")
        self.a.arquivo("ops/systemd/fixture.service",
                       "[Service]\nExecStart=/opt/x/tools/check-coisa\n")
        self.a.registro([{"ferramenta": "tools/check-coisa", "classe": "datado",
                          "destino": "arquivar-migracao-datada", "motivo": "migracao",
                          "decidido_em": "2026-09-16"}])
        rc, saida = self.a.roda()
        self.assertEqual(rc, 1, f"linha obsoleta tinha de reprovar; saida:\n{saida}")
        self.assertIn("JA TEM executor", saida)

    # ------------------------------------------------------ wrapper de gate Go
    def test_wrapper_de_gate_registrado_nao_e_orfao(self):
        self.a.detector("tools-run-check-fake")  # so para popular a arvore
        escreve(os.path.join(self.a.raiz, "tools/run-check"),
                "#!/usr/bin/env bash\nexit 0\n", True)
        self.a.detector("check-gate-real",
                        '#!/usr/bin/env bash\nexec "$ROOT/tools/run-check" gate-real "$@"\n')
        self.a.arquivo("internal/checks/checks.go",
                       'package checks\n\nvar Names = []string{\n\t"gate-real",\n}\n')
        # a rotacao tem de estar viva: e' ela quem executa o gate Go
        escreve(os.path.join(self.a.raiz, "tools/run-gates-rotativos"),
                "#!/usr/bin/env python3\nprint('rotacao')\n", True)
        self.a.arquivo("ops/systemd/fixture.service",
                       "[Service]\nExecStart=/opt/x/tools/run-gates-rotativos\n")
        censo = self.a.censo()
        self.assertIn("tools/check-gate-real", censo["wrappers_de_gate_go"],
                      "wrapper de gate registrado tem o predicado rodando na rotacao")
        self.assertNotIn("tools/check-gate-real", censo["orfaos"])

    def test_wrapper_volta_a_ser_orfao_quando_a_rotacao_sai_do_ar(self):
        """A cobertura do wrapper e' CONDICIONAL, e a condicao e' medida."""
        escreve(os.path.join(self.a.raiz, "tools/run-check"), "#!/usr/bin/env bash\nexit 0\n", True)
        self.a.detector("check-gate-real",
                        '#!/usr/bin/env bash\nexec "$ROOT/tools/run-check" gate-real "$@"\n')
        self.a.arquivo("internal/checks/checks.go",
                       'package checks\n\nvar Names = []string{\n\t"gate-real",\n}\n')
        escreve(os.path.join(self.a.raiz, "tools/run-gates-rotativos"),
                "#!/usr/bin/env python3\nprint('rotacao')\n", True)
        # SEM unit: a rotacao existe no disco e nao e' acionada por ninguem.
        censo = self.a.censo()
        self.assertFalse(censo["rotacao_viva"])
        self.assertIn("tools/check-gate-real", censo["orfaos"],
                      "sem rotacao acionada, o wrapper nao tem quem rode o predicado")

    def test_comentario_dentro_do_bloco_names_nao_vira_nome_de_gate(self):
        """As palavras 'atrasada', 'passou' e 'saudavel' vivem em comentario no
        bloco `var Names` do repo real. Sem cortar comentario, um wrapper que
        passasse `run-check passou` seria absolvido por uma palavra em portugues."""
        escreve(os.path.join(self.a.raiz, "tools/run-check"), "#!/usr/bin/env bash\nexit 0\n", True)
        self.a.detector("check-gate-falso",
                        '#!/usr/bin/env bash\nexec "$ROOT/tools/run-check" passou "$@"\n')
        self.a.arquivo("internal/checks/checks.go",
                       'package checks\n\nvar Names = []string{\n\t// a etapa "passou" quando o ledger\n\t"gate-real",\n}\n')
        escreve(os.path.join(self.a.raiz, "tools/run-gates-rotativos"),
                "#!/usr/bin/env python3\nprint('x')\n", True)
        self.a.arquivo("ops/systemd/fixture.service",
                       "[Service]\nExecStart=/opt/x/tools/run-gates-rotativos\n")
        censo = self.a.censo()
        self.assertIn("tools/check-gate-falso", censo["orfaos"],
                      "nome vindo de comentario nao pode absolver wrapper nenhum")


if __name__ == "__main__":
    unittest.main(verbosity=2)
