#!/usr/bin/env python3
"""Bancada de tools/check-memoria-no-limite.

O que esta guarda protege e um corte que nao aparece em log nem em exit code:
passado o teto, o excedente do MEMORY.md deixa de carregar em toda sessao
seguinte (o CLI so acrescenta um "> WARNING:" ao conteudo carregado, que o
modelo ve e o disco nao). Logo o teste tem de provar tres coisas, e cada uma
mata um mutante que ja esteve VIVO nesta ferramenta:

1. O alarme soa ANTES do corte -- alarme no teto reprova depois do dano.
2. A grandeza medida e' UNIDADE UTF-16 (`n.length` do JS), nao byte UTF-8. A
   primeira versao desta guarda media byte, e em PT-BR acentuado byte e unidade
   divergem ~3,4%: o mutante "mede bytes" passa despercebido num indice ASCII e
   so morre com fixture ACENTUADA.
3. O teto e' 25.000, nao 25*1024. O mutante que sobe o alarme ate 25.600 morre
   na fixture da faixa util.

E, porque compactar indice mexe em ponteiro, a bancada cobre tambem os defeitos
de ponteiro -- inclusive o FALSO POSITIVO real: `[[ $x =~ $re ]]` do bash, que
existe em ai-terminal-claude-first.md e nao e' wikilink.

PROVA POR MUTACAO (rodada em 2026-09-16, com `python3 -B` para nao servir .pyc
velho): ALARME_CHARS=25000 mata test_reprova_por_unidades...; medir
`len(bruto)` no lugar de unidades_utf16 mata test_acentuado...; devolver o texto
cru em sem_codigo() mata test_wikilink_em_bloco_de_codigo...; ignorar
citadas_em_rules mata test_memoria_absorvida_por_rule_nao_e_orfa.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FERRAMENTA = RAIZ / "tools" / "check-memoria-no-limite"

spec = importlib.util.spec_from_loader(
    "check_memoria_no_limite",
    importlib.machinery.SourceFileLoader("check_memoria_no_limite", str(FERRAMENTA)),
)
MOD = importlib.util.module_from_spec(spec)
spec.loader.exec_module(MOD)

CABECALHO = "---\nname: {slug}\ndescription: fixture\nmetadata:\n  type: project\n---\n\n"


class Arvore:
    """~/.claude/projects/<slug>/memory/ + <projeto>/.claude/rules/ de mentira."""

    def __init__(self) -> None:
        self.base = Path(tempfile.mkdtemp(prefix="memoria-teto-"))
        self.projeto = self.base / "repo"
        self.projeto.mkdir()
        slug = str(self.projeto).replace("/", "-")
        self.memdir = self.base / "cfg" / "projects" / slug / "memory"
        self.memdir.mkdir(parents=True)
        self.cfg = self.base / "cfg"
        self.linhas: list[str] = []

    def memoria(self, nome: str, corpo: str = "", no_indice: bool = True) -> "Arvore":
        slug = nome[:-3]
        (self.memdir / nome).write_text(CABECALHO.format(slug=slug) + corpo + "\n", encoding="utf-8")
        if no_indice:
            self.linhas.append(f"- [{slug}]({nome}) — fixture")
        return self

    def rule(self, nome: str, corpo: str) -> "Arvore":
        destino = self.projeto / ".claude" / "rules"
        destino.mkdir(parents=True, exist_ok=True)
        (destino / nome).write_text(corpo + "\n", encoding="utf-8")
        return self

    def indice(self, texto: str | None = None) -> "Arvore":
        corpo = texto if texto is not None else "\n".join(self.linhas)
        (self.memdir / "MEMORY.md").write_text(corpo + "\n", encoding="utf-8")
        return self

    def tamanho_do_indice(self) -> tuple[int, int, int]:
        bruto = (self.memdir / "MEMORY.md").read_bytes()
        trimado = bruto.decode("utf-8").strip()
        return (trimado.count("\n") + 1, MOD.unidades_utf16(trimado), len(bruto))

    def roda(self) -> subprocess.CompletedProcess:
        env = dict(
            os.environ,
            CLAUDE_PROJECT_DIR=str(self.projeto),
            CLAUDE_CONFIG_DIR=str(self.cfg),
            PYTHONDONTWRITEBYTECODE="1",
        )
        return subprocess.run(
            [sys.executable, "-B", str(FERRAMENTA)], capture_output=True, text=True, env=env
        )

    def limpa(self) -> None:
        shutil.rmtree(self.base, ignore_errors=True)


def arvore_de_indice(linhas: int, enchimento: str) -> Arvore:
    """Indice sintetico com N linhas de ponteiro, cada uma com destino PROPRIO.

    Destino repetido seria ponteiro duplicado -- defeito que a guarda reprova com
    razao, e que na primeira versao desta bancada reprovava a fixture inteira.
    """
    a = Arvore()
    for i in range(linhas):
        a.memoria(f"m{i}.md", no_indice=False)
    corpo = "\n".join(f"- [t{i}](m{i}.md) — {enchimento}" for i in range(linhas))
    return a.indice(corpo)


class TesteAlarmeAntesDoCorte(unittest.TestCase):
    def setUp(self) -> None:
        self.arvores: list[Arvore] = []

    def tearDown(self) -> None:
        for a in self.arvores:
            a.limpa()

    def registra(self, a: Arvore) -> Arvore:
        self.arvores.append(a)
        return a

    def test_reprova_por_linhas_antes_do_corte_oficial(self):
        """190 linhas reprova; o corte oficial so viria em 200."""
        a = self.registra(arvore_de_indice(MOD.ALARME_LINHAS, "x" * 20))
        linhas, chars, _ = a.tamanho_do_indice()
        self.assertEqual(linhas, MOD.ALARME_LINHAS)
        self.assertLess(chars, MOD.ALARME_CHARS, "a fixture tem de morder so o eixo de linhas")
        proc = a.roda()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn(f"linhas {MOD.ALARME_LINHAS}", proc.stderr)

    def test_reprova_por_unidades_antes_do_corte_oficial(self):
        """O eixo de tamanho morde ENTRE o alarme (23.750) e o corte (25.000).

        Mutante que este teste mata: subir ALARME_CHARS ate o teto de 25.000, ou
        ate os 25.600 da leitura errada de "25 KB" -- a fixture fica na faixa em
        que os dois vereditos divergem.
        """
        a = self.registra(arvore_de_indice(40, "x" * 590))
        linhas, chars, _ = a.tamanho_do_indice()
        self.assertTrue(
            MOD.ALARME_CHARS <= chars < MOD.TETO_CHARS_OFICIAL,
            f"fixture fora da faixa util: {chars} nao esta entre "
            f"{MOD.ALARME_CHARS} e {MOD.TETO_CHARS_OFICIAL}",
        )
        self.assertLess(linhas, MOD.ALARME_LINHAS)
        proc = a.roda()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("unidades", proc.stderr)
        self.assertNotIn(f"linhas {linhas} >=", proc.stderr)

    def test_indice_acentuado_abaixo_do_teto_em_unidades_passa(self):
        """MATA O MUTANTE DA UNIDADE: quem mede byte UTF-8 reprova esta fixture.

        Portugues acentuado custa 2 bytes por caractere. A fixture fica abaixo do
        alarme em UNIDADE (que e' o que o CLI corta) e acima do teto antigo em
        BYTE -- exatamente o caso do indice real deste projeto, so que amplificado
        para tornar o mutante visivel.
        """
        a = self.registra(arvore_de_indice(60, "ç" * 340))
        linhas, chars, bytes_ = a.tamanho_do_indice()
        self.assertLess(chars, MOD.ALARME_CHARS, "a fixture tem de estar FOLGADA em unidades")
        self.assertGreater(bytes_, 25 * 1024, "sem isso o mutante 'mede bytes' sobrevive")
        self.assertLess(linhas, MOD.AVISO_LINHAS)
        proc = a.roda()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("unidades UTF-16", proc.stdout)

    def test_indice_folgado_passa_e_diz_a_folga(self):
        a = self.registra(arvore_de_indice(60, "x" * 80))
        proc = a.roda()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("folga ate o alarme", proc.stdout)
        self.assertIn("folga ate o corte", proc.stdout)

    def test_bem_abaixo_do_alarme_nao_reprova(self):
        """Controle negativo: sem ele, guarda que reprova sempre passaria acima."""
        a = self.registra(arvore_de_indice(10, "x" * 30))
        self.assertEqual(a.roda().returncode, 0)

    def test_aviso_do_vendor_aparece_sem_reprovar(self):
        """160 linhas e' o 0.8 do proprio CLI: avisa, nao reprova."""
        a = self.registra(arvore_de_indice(MOD.AVISO_LINHAS + 2, "x" * 20))
        proc = a.roda()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("approaching the read limit", proc.stdout)
        self.assertIn(str(MOD.META_LINHAS), proc.stdout)


class TesteDefeitosDePonteiro(unittest.TestCase):
    def setUp(self) -> None:
        self.arvores: list[Arvore] = []

    def tearDown(self) -> None:
        for a in self.arvores:
            a.limpa()

    def registra(self, a: Arvore) -> Arvore:
        self.arvores.append(a)
        return a

    def test_ponteiro_quebrado_reprova(self):
        a = self.registra(Arvore())
        a.memoria("existe.md")
        a.indice("\n".join(a.linhas + ["- [some](sumiu.md) — alvo inexistente"]))
        proc = a.roda()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("ponteiro quebrado", proc.stderr)
        self.assertIn("sumiu.md", proc.stderr)

    def test_memoria_orfa_reprova(self):
        a = self.registra(Arvore())
        a.memoria("no-indice.md")
        a.memoria("fora-do-indice.md", no_indice=False)
        a.indice()
        proc = a.roda()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("memoria orfa", proc.stderr)
        self.assertIn("fora-do-indice.md", proc.stderr)

    def test_memoria_absorvida_por_rule_nao_e_orfa(self):
        """A rota da compactacao: a linha sai do indice e a rule passa a carregar.

        MATA O MUTANTE que ignora .claude/rules/ -- sem esta leitura, toda
        memoria migrada vira orfa e a propria correcao fica proibida.
        """
        a = self.registra(Arvore())
        a.memoria("no-indice.md")
        a.memoria("absorvida.md", no_indice=False)
        a.rule(
            "trap.md",
            "---\npaths:\n  - \"data/x.json\"\n---\n\n# trap\n\nMemoria de origem: `absorvida.md`.",
        )
        a.indice()
        proc = a.roda()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("absorvidas por rule: 1", proc.stdout)
        self.assertIn("orfas: 0", proc.stdout)

    def test_wikilink_em_bloco_de_codigo_nao_conta(self):
        """Falso positivo REAL: `[[ $x =~ $re ]]` existe em ai-terminal-claude-first.md.

        A fixture nao se contenta com o bash: ela poe dentro da crase e dentro do
        bloco um QUASE-HOMONIMO do arquivo existente. Sem apagar codigo, esses
        dois casariam como deriva de nome e a guarda reprovaria — e' esse o
        mutante que este teste mata. A primeira versao usava so o bash, que cai
        na faixa "referencia futura" e deixava o mutante VIVO: fixture fraca
        denuncia a fixture, nao o predicado.
        """
        a = self.registra(Arvore())
        a.memoria("alvo-real.md")
        a.memoria(
            "com-bash.md",
            "Use `[[ $x =~ $re ]]` e `[[alvo-reall]]` para casar, e no bloco:\n\n"
            "```bash\nif [[ -e f ]]; then :; fi\n[[alvo-reeal]]\n```\n\nVer [[alvo-real]].",
        )
        a.indice()
        proc = a.roda()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn("deriva de nome:", proc.stderr)
        self.assertIn("[[links]] por deriva de nome: 0", proc.stdout)
        self.assertNotIn("alvo-reall", proc.stdout + proc.stderr)
        self.assertNotIn("alvo-reeal", proc.stdout + proc.stderr)

    def test_wikilink_por_deriva_de_nome_reprova(self):
        a = self.registra(Arvore())
        a.memoria("commit-sob-flock-pega-indice-do-futuro.md")
        a.memoria("cita.md", "Ver [[commit-sob-flock-indice-do-futuro]].")
        a.indice()
        proc = a.roda()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("deriva de nome", proc.stderr)

    def test_wikilink_sem_quase_homonimo_e_referencia_futura(self):
        """O manual da memoria autoriza link para memoria ainda nao escrita."""
        a = self.registra(Arvore())
        a.memoria("alvo-real.md")
        a.memoria("cita.md", "Ver [[memoria-que-ninguem-escreveu-ainda]].")
        a.indice()
        proc = a.roda()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("referencia futura", proc.stdout)


class TesteNaoMedido(unittest.TestCase):
    def test_indice_ausente_sai_2_e_nao_1(self):
        """Ausencia e 'nao medi', nunca veredito.

        Exit 1 aqui seria pior que inutil: as units deste repo mascaram o 1
        como veredito medido, entao 'nao achei o arquivo' viraria sucesso.
        """
        base = Path(tempfile.mkdtemp(prefix="memoria-vazia-"))
        try:
            env = dict(
                os.environ,
                CLAUDE_PROJECT_DIR=str(base / "repo-inexistente"),
                CLAUDE_CONFIG_DIR=str(base / "cfg"),
            )
            proc = subprocess.run(
                [sys.executable, "-B", str(FERRAMENTA)], capture_output=True, text=True, env=env
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("NAO MEDIDO", proc.stderr)
        finally:
            shutil.rmtree(base, ignore_errors=True)


class TesteContraOBinarioVivo(unittest.TestCase):
    """Os tetos desta guarda sao leitura do CLI instalado, nao da documentacao.

    Se um build novo trocar a constante, este teste fica vermelho e o teto tem
    de ser remedido -- a alternativa e a guarda envelhecer sem ninguem notar.
    """

    def test_constantes_batem_com_o_bundle_do_cli(self):
        versoes = Path.home() / ".local" / "share" / "claude" / "versions"
        binarios = sorted(p for p in versoes.glob("*") if p.is_file()) if versoes.is_dir() else []
        if not binarios:
            self.skipTest(f"NAO MEDIDO: nenhum bundle do CLI em {versoes}")
        alvo = binarios[-1]
        padrao = rf"=({MOD.TETO_LINHAS_OFICIAL}),[A-Za-z0-9_$]{{1,4}}=({MOD.TETO_CHARS_OFICIAL}),"
        proc = subprocess.run(
            ["grep", "-a", "-c", "-E", padrao, str(alvo)], capture_output=True, text=True
        )
        self.assertEqual(
            proc.returncode,
            0,
            f"o bundle {alvo.name} nao declara mais '{MOD.TETO_LINHAS_OFICIAL} linhas / "
            f"{MOD.TETO_CHARS_OFICIAL} unidades' — remeça o teto antes de confiar nesta guarda",
        )
        self.assertEqual(proc.stdout.strip(), "1", "esperado exatamente um ponto de declaracao")


class TesteEstadoReal(unittest.TestCase):
    """Mede o indice do projeto de verdade, sem env forjado.

    ARMADILHA AO LER PROVA POR MUTACAO: rodando esta bancada de uma COPIA da
    arvore (o jeito seguro de mutar sem deixar a guarda viva mutada), a
    ferramenta resolve `CLAUDE_PROJECT_DIR` para a copia, nao acha indice nenhum
    e sai 2 -- entao este teste reprova para TODO mutante, inclusive o inocente.
    E' fail-closed (nunca verde por ausencia), mas nao serve para atribuir morte:
    o mutante so esta morto se um teste DEDICADO reprovar.
    """

    def test_indice_do_projeto_esta_abaixo_do_alarme(self):
        proc = subprocess.run(
            [sys.executable, "-B", str(FERRAMENTA)], capture_output=True, text=True
        )
        self.assertEqual(
            proc.returncode,
            0,
            "o indice de memoria deste projeto passou do alarme:\n" + proc.stdout + proc.stderr,
        )

    def test_ferramenta_e_read_only(self):
        fonte = FERRAMENTA.read_text(encoding="utf-8")
        for proibido in ("write_text(", "write_bytes(", "os.remove", "shutil.rmtree", "os.rename"):
            self.assertNotIn(proibido, fonte, f"a guarda nao pode escrever: achei {proibido}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
